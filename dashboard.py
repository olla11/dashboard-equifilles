"""
================================================================================
  DASHBOARD DE PILOTAGE S&E — VERSION V6
  ONG Equi-Filles — Projets EQUIFILLES (FoSIR) & SPACE TO LEAD (Plan Int.)
--------------------------------------------------------------------------------
  Lit directement depuis Google Sheets (onglet 'K. Données Kobo' unifié).
  5 pages : Vue d'ensemble · Par type · Indicateurs · Finances · Cartographie.
  3 profils : direction, bailleur, equipe.

  LANCEMENT LOCAL :
    pip install -r requirements.txt
    streamlit run dashboard.py

  DÉPLOIEMENT STREAMLIT CLOUD :
    1. Pousser dashboard.py + requirements.txt sur GitHub
    2. Sur share.streamlit.io, créer une app pointant sur le repo
    3. Dans Settings > Secrets, coller la configuration (voir plus bas)
================================================================================
"""

import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ============================================================================
#  1. CONFIGURATION
# ============================================================================

# ID du Google Sheets (extrait de l'URL entre /d/ et /edit)
# En local : renseigner ici. En cloud : mettre dans les secrets.
GOOGLE_SHEET_ID = "15PsPjcQBLa90svPxtlixlKPQH_zYMXfhtQuj-Si1miQ"

# Onglet unique de source
ONGLET_KOBO = "K. Données Kobo"

# Palette Equi-Filles
COLORS = {
    "PRIMARY": "#C00000",      # Rouge EQUIFILLES
    "SECONDARY": "#00B050",    # Vert S2L
    "TERTIARY": "#1F3864",     # Bleu marine
    "ACCENT": "#BF8F00",       # Or (accent)
    "BG": "#FAFAFA",
    "TEXT": "#1F2937",
    "MUTE": "#6B7280",
    "SUCCESS": "#70AD47",
    "WARNING": "#ED7D31",
    "DANGER": "#C00000",
}

# 3 profils de login (mot de passe simple pour cette V6, à durcir ensuite)
PROFILS = {
    "direction": {
        "mdp": "direction2026",
        "nom": "Direction (DE)",
        "pages": ["Vue d'ensemble", "Par type d'activité", "Indicateurs & Résultats", "Finances", "Cartographie"],
    },
    "bailleur": {
        "mdp": "bailleur2026",
        "nom": "Bailleurs (FoSIR / Plan Int.)",
        "pages": ["Vue d'ensemble", "Indicateurs & Résultats", "Finances"],
    },
    "equipe": {
        "mdp": "equipe2026",
        "nom": "Équipe terrain",
        "pages": ["Vue d'ensemble", "Par type d'activité", "Cartographie"],
    },
}

# Correspondance des 8 types d'activités (codes réels du formulaire Kobo)
TYPES_ACTIVITE = {
    "etudes":      "📚 Études, recherche & diagnostics",
    "sensib_mob":  "📣 Sensibilisation, communication & mobilisation",
    "form_acc":    "🎓 Formation, coaching & accompagnement",
    "plaidoyer":   "🗣️ Plaidoyer, dialogue & gouvernance",
    "appui_benef": "🤝 Appui aux bénéficiaires",
    "meal":        "📊 Suivi-évaluation & capitalisation",
    "gouv_coord":  "🏛️ Gouvernance, coordination & partenariats",
    "autre":       "📌 Autre",
}

# Correspondance projets
PROJETS = {
    "fosir":         "EQUIFILLES (FoSIR)",
    "space_to_lead": "SPACE TO LEAD (Plan Int.)",
    "autre":         "Autre",
}

# Coordonnées approximatives des communes du Bénin (fallback si GPS vide)
COMMUNES_GPS = {
    "gogounou":    (10.83, 2.83),
    "malanville":  (11.86, 3.38),
    "karimama":    (12.06, 3.19),
    "banikoara":   (11.29, 2.44),
    "kandi":       (11.13, 2.94),
    "segbana":     (10.93, 3.70),
    "cotonou":     (6.37, 2.42),
    "parakou":     (9.34, 2.62),
    "natitingou":  (10.32, 1.38),
    "porto-novo":  (6.50, 2.60),
}


# ============================================================================
#  2. CONFIGURATION STREAMLIT
# ============================================================================
st.set_page_config(
    page_title="S&E Equi-Filles",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS custom pour appliquer la palette
st.markdown(f"""
<style>
    .main {{ background-color: {COLORS['BG']}; }}
    .stMetric {{
        background-color: white;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid {COLORS['PRIMARY']};
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    h1, h2, h3 {{ color: {COLORS['TERTIARY']}; }}
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
        font-weight: 600;
    }}
    div[data-testid="stSidebar"] {{
        background-color: white;
        border-right: 2px solid #E5E7EB;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================================
#  3. LECTURE DES DONNÉES GOOGLE SHEETS
# ============================================================================
@st.cache_data(ttl=300, show_spinner="Chargement des données...")
def charger_donnees(sheet_id: str) -> pd.DataFrame:
    """Lit l'onglet K. Données Kobo depuis Google Sheets publié."""
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={ONGLET_KOBO}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        # Lecture brute sans en-tête : on prendra les colonnes B à AC (indices 1 à 28)
        df_raw = pd.read_csv(io.StringIO(r.text), header=None, dtype=str)
        return _nettoyer_df(df_raw)
    except Exception as e:
        st.error(f"❌ Erreur lecture Google Sheets : {e}")
        st.info(
            "Vérifiez que le classeur est bien publié : "
            "**Fichier > Partager > Publier sur le web > Publier**"
        )
        return pd.DataFrame()


def _nettoyer_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Nettoie le DataFrame : cherche la vraie zone de données à partir de
    la colonne submission_id (nombres) puis type des colonnes."""
    if df_raw.empty or df_raw.shape[1] < 2:
        return pd.DataFrame()

    # Les données de K. Données Kobo commencent à la colonne B (index 1)
    # et à la ligne 13 dans le fichier — mais gviz réindexe, on ne peut pas
    # se fier aux numéros de ligne. On cherche la 1ère ligne où la colonne B
    # (submission_id) contient un nombre à plusieurs chiffres.
    col_id = df_raw.iloc[:, 1]  # Colonne B
    ligne_debut = None
    for idx, val in col_id.items():
        s = str(val).strip()
        if s.isdigit() and len(s) >= 6:  # submission_id Kobo = 9 chiffres
            ligne_debut = idx
            break

    if ligne_debut is None:
        return pd.DataFrame()

    # Extraire les données à partir de la ligne détectée
    df = df_raw.iloc[ligne_debut:, 1:29].copy()  # Colonnes B à AC = 28 colonnes

    # Nommer les colonnes
    noms_colonnes = [
        "submission_id", "type_activite", "nom_projet", "date_remplissage",
        "periode_mo", "nom_activite", "date_debut", "date_fin", "nombre_jours",
        "responsable", "budget", "departement", "commune", "arrondissement",
        "village", "gps", "f_total", "h_total", "part_10_14", "part_15_17",
        "total_beneficiaires", "grand_resultat", "difficultes", "satis_global",
        "photos_nb", "has_liste_pres", "has_rapport", "has_autres_doc",
    ]
    df.columns = noms_colonnes[:df.shape[1]]

    # Retirer les lignes sans type_activite
    df = df[df["type_activite"].notna() & (df["type_activite"].astype(str).str.strip() != "")]

    # Typer les dates
    for col in ["date_remplissage", "periode_mo", "date_debut", "date_fin"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # Typer les entiers
    for col in ["nombre_jours", "budget", "f_total", "h_total",
                "part_10_14", "part_15_17", "total_beneficiaires", "photos_nb"]:
        if col in df.columns:
            df[col] = (df[col].astype(str)
                              .str.replace(" ", "")
                              .str.replace(",", ".")
                              .replace(["", "nan", "None"], "0"))
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df.reset_index(drop=True)


# ============================================================================
#  4. AUTHENTIFICATION (login simple)
# ============================================================================
def afficher_login():
    """Écran de login initial."""
    st.markdown(f"""
    <div style='text-align: center; padding: 40px 20px 20px 20px;'>
        <h1 style='color: {COLORS['PRIMARY']}; margin-bottom: 5px;'>
            ONG Equi-Filles
        </h1>
        <p style='color: {COLORS['MUTE']}; font-size: 16px; margin-top: 0;'>
            Système intégré de Suivi-Évaluation
        </p>
        <p style='color: {COLORS['TERTIARY']}; font-size: 14px; font-style: italic;'>
            Projets EQUIFILLES (FoSIR) &amp; SPACE TO LEAD (Plan International)
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Connexion")
        profil = st.selectbox(
            "Profil",
            options=list(PROFILS.keys()),
            format_func=lambda x: PROFILS[x]["nom"],
        )
        mdp = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", type="primary", use_container_width=True):
            if mdp == PROFILS[profil]["mdp"]:
                st.session_state["profil"] = profil
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")

        with st.expander("ℹ️ Identifiants de test (à remplacer en prod)"):
            st.code("""direction / direction2026
bailleur  / bailleur2026
equipe    / equipe2026""", language=None)


# ============================================================================
#  5. FILTRES DE LA SIDEBAR
# ============================================================================
def appliquer_filtres(df: pd.DataFrame) -> pd.DataFrame:
    """Affiche les filtres et retourne le DataFrame filtré."""
    st.sidebar.markdown("### 🔍 Filtres")

    # Filtre projet
    projets_dispo = sorted(df["nom_projet"].dropna().unique().tolist())
    projet_sel = st.sidebar.multiselect(
        "Projet",
        options=projets_dispo,
        default=projets_dispo,
        format_func=lambda x: PROJETS.get(x, x),
    )
    if projet_sel:
        df = df[df["nom_projet"].isin(projet_sel)]

    # Filtre type d'activité
    types_dispo = sorted(df["type_activite"].dropna().unique().tolist())
    type_sel = st.sidebar.multiselect(
        "Type d'activité",
        options=types_dispo,
        default=types_dispo,
        format_func=lambda x: TYPES_ACTIVITE.get(x, x),
    )
    if type_sel:
        df = df[df["type_activite"].isin(type_sel)]

    # Filtre commune
    if "commune" in df.columns:
        communes_dispo = sorted(df["commune"].dropna().unique().tolist())
        if communes_dispo:
            commune_sel = st.sidebar.multiselect(
                "Commune",
                options=communes_dispo,
                default=[],
                help="Laisser vide pour toutes les communes",
            )
            if commune_sel:
                df = df[df["commune"].isin(commune_sel)]

    # Filtre période
    if "date_debut" in df.columns and df["date_debut"].notna().any():
        st.sidebar.markdown("**Période**")
        d_min = df["date_debut"].min()
        d_max = df["date_debut"].max()
        if pd.notna(d_min) and pd.notna(d_max):
            date_debut = st.sidebar.date_input(
                "Du", value=d_min.date(), min_value=d_min.date(), max_value=d_max.date(),
            )
            date_fin = st.sidebar.date_input(
                "Au", value=d_max.date(), min_value=d_min.date(), max_value=d_max.date(),
            )
            df = df[
                (df["date_debut"] >= pd.Timestamp(date_debut)) &
                (df["date_debut"] <= pd.Timestamp(date_fin))
            ]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"📊 **{len(df)}** activité(s) affichée(s)")
    return df


# ============================================================================
#  6. PAGE — VUE D'ENSEMBLE
# ============================================================================
def page_vue_ensemble(df: pd.DataFrame):
    st.markdown("## 🏠 Vue d'ensemble")
    st.caption("Situation consolidée des deux projets")

    # KPI en 4 colonnes
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Activités", f"{len(df):,}".replace(",", " "))
    c2.metric("👥 Bénéficiaires", f"{int(df['total_beneficiaires'].sum()):,}".replace(",", " "))
    c3.metric("💰 Budget total", f"{int(df['budget'].sum()):,}".replace(",", " ") + " FCFA")
    c4.metric("⏱️ Jours d'action", f"{int(df['nombre_jours'].sum()):,}".replace(",", " "))

    st.markdown("---")

    # 2 graphiques côte à côte
    col_g, col_d = st.columns(2)

    with col_g:
        st.markdown("#### 📊 Activités par type")
        if not df.empty:
            dfg = df.groupby("type_activite").size().reset_index(name="count")
            dfg["label"] = dfg["type_activite"].map(TYPES_ACTIVITE).fillna(dfg["type_activite"])
            fig = px.bar(
                dfg.sort_values("count"),
                x="count", y="label", orientation="h",
                color_discrete_sequence=[COLORS["PRIMARY"]],
                labels={"count": "Nombre d'activités", "label": ""},
            )
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher.")

    with col_d:
        st.markdown("#### 🥧 Répartition par projet")
        if not df.empty:
            dfp = df.groupby("nom_projet")["total_beneficiaires"].sum().reset_index()
            dfp["label"] = dfp["nom_projet"].map(PROJETS).fillna(dfp["nom_projet"])
            fig = px.pie(
                dfp, values="total_beneficiaires", names="label",
                color_discrete_sequence=[COLORS["PRIMARY"], COLORS["SECONDARY"], COLORS["ACCENT"]],
                hole=0.4,
            )
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher.")

    st.markdown("---")

    # Activités récentes
    st.markdown("#### 🕒 Dernières activités enregistrées")
    if not df.empty:
        cols_affichage = ["date_remplissage", "type_activite", "nom_activite",
                          "nom_projet", "commune", "total_beneficiaires", "budget"]
        cols_dispo = [c for c in cols_affichage if c in df.columns]
        df_recent = df.sort_values("date_remplissage", ascending=False).head(10)
        df_recent = df_recent[cols_dispo].copy()
        df_recent["type_activite"] = df_recent["type_activite"].map(TYPES_ACTIVITE).fillna(df_recent["type_activite"])
        df_recent["nom_projet"] = df_recent["nom_projet"].map(PROJETS).fillna(df_recent["nom_projet"])
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune activité enregistrée.")


# ============================================================================
#  7. PAGE — PAR TYPE D'ACTIVITÉ
# ============================================================================
def page_par_type(df: pd.DataFrame):
    st.markdown("## 📁 Analyse par type d'activité")

    if df.empty:
        st.info("Aucune activité disponible.")
        return

    # Onglets par type
    types_presents = sorted(df["type_activite"].dropna().unique().tolist())
    if not types_presents:
        st.info("Aucun type d'activité dans les données filtrées.")
        return

    tabs = st.tabs([TYPES_ACTIVITE.get(t, t) for t in types_presents])
    for i, type_code in enumerate(types_presents):
        with tabs[i]:
            df_t = df[df["type_activite"] == type_code]

            # KPI
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Activités", len(df_t))
            c2.metric("Bénéficiaires", f"{int(df_t['total_beneficiaires'].sum()):,}".replace(",", " "))
            c3.metric("Budget", f"{int(df_t['budget'].sum()):,}".replace(",", " ") + " FCFA")
            c4.metric("Durée cumulée", f"{int(df_t['nombre_jours'].sum())} j")

            # Désagrégation F/H
            col_g, col_d = st.columns([1, 2])
            with col_g:
                st.markdown("##### 👥 Femmes / Hommes")
                total_f = int(df_t["f_total"].sum())
                total_h = int(df_t["h_total"].sum())
                if total_f + total_h > 0:
                    fig = go.Figure(data=[go.Pie(
                        labels=["Femmes/filles", "Hommes/garçons"],
                        values=[total_f, total_h],
                        marker_colors=[COLORS["PRIMARY"], COLORS["TERTIARY"]],
                        hole=0.5,
                    )])
                    fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Pas de données F/H")

            with col_d:
                st.markdown("##### 📋 Liste des activités")
                cols = ["nom_activite", "commune", "responsable", "total_beneficiaires", "budget"]
                cols_dispo = [c for c in cols if c in df_t.columns]
                st.dataframe(df_t[cols_dispo], use_container_width=True, hide_index=True, height=260)


# ============================================================================
#  8. PAGE — INDICATEURS & RÉSULTATS
# ============================================================================
def page_indicateurs(df: pd.DataFrame):
    st.markdown("## 📊 Indicateurs & Résultats")
    st.caption("Suivi des indicateurs des deux projets")

    if df.empty:
        st.info("Aucune donnée disponible.")
        return

    # 3 sous-onglets : Global · EQUIFILLES · S2L
    tab1, tab2, tab3 = st.tabs(["📈 Global", "🔴 EQUIFILLES", "🟢 SPACE TO LEAD"])

    with tab1:
        _sous_page_indicateurs_global(df)

    with tab2:
        df_eq = df[df["nom_projet"] == "fosir"]
        _sous_page_indicateurs_projet(df_eq, "EQUIFILLES (FoSIR)", COLORS["PRIMARY"])

    with tab3:
        df_s2l = df[df["nom_projet"] == "space_to_lead"]
        _sous_page_indicateurs_projet(df_s2l, "SPACE TO LEAD", COLORS["SECONDARY"])


def _sous_page_indicateurs_global(df: pd.DataFrame):
    st.markdown("### 📊 Indicateurs consolidés")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total bénéficiaires", f"{int(df['total_beneficiaires'].sum()):,}".replace(",", " "))

    total_f = int(df["f_total"].sum())
    total_h = int(df["h_total"].sum())
    part_f = (total_f / (total_f + total_h) * 100) if (total_f + total_h) > 0 else 0
    c2.metric("Part femmes/filles", f"{part_f:.1f}%")

    jeunes = int(df["part_10_14"].sum() + df["part_15_17"].sum())
    c3.metric("Jeunes (10-17 ans)", f"{jeunes:,}".replace(",", " "))

    st.markdown("---")

    # Évolution mensuelle
    if "date_debut" in df.columns and df["date_debut"].notna().any():
        st.markdown("#### 📈 Évolution mensuelle")
        df_ev = df.copy()
        df_ev["mois"] = df_ev["date_debut"].dt.to_period("M").astype(str)
        df_mens = df_ev.groupby("mois").agg(
            activites=("submission_id", "count"),
            beneficiaires=("total_beneficiaires", "sum"),
        ).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_mens["mois"], y=df_mens["activites"],
            name="Activités", marker_color=COLORS["PRIMARY"],
        ))
        fig.add_trace(go.Scatter(
            x=df_mens["mois"], y=df_mens["beneficiaires"],
            name="Bénéficiaires", yaxis="y2",
            line=dict(color=COLORS["SECONDARY"], width=3),
            mode="lines+markers",
        ))
        fig.update_layout(
            height=400,
            yaxis=dict(title="Activités"),
            yaxis2=dict(title="Bénéficiaires", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)


def _sous_page_indicateurs_projet(df: pd.DataFrame, nom_projet: str, couleur: str):
    st.markdown(f"### {nom_projet}")
    if df.empty:
        st.info(f"Aucune activité pour {nom_projet} dans les filtres actuels.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Activités", len(df))
    c2.metric("Bénéficiaires", f"{int(df['total_beneficiaires'].sum()):,}".replace(",", " "))
    c3.metric("Budget", f"{int(df['budget'].sum()):,}".replace(",", " ") + " FCFA")
    total_f = int(df["f_total"].sum())
    total_h = int(df["h_total"].sum())
    part_f = (total_f / (total_f + total_h) * 100) if (total_f + total_h) > 0 else 0
    c4.metric("% femmes/filles", f"{part_f:.1f}%")

    # Bénéficiaires par type d'activité
    st.markdown("#### 👥 Bénéficiaires par type d'activité")
    df_ag = df.groupby("type_activite")["total_beneficiaires"].sum().reset_index()
    df_ag["label"] = df_ag["type_activite"].map(TYPES_ACTIVITE).fillna(df_ag["type_activite"])
    fig = px.bar(
        df_ag.sort_values("total_beneficiaires"),
        x="total_beneficiaires", y="label", orientation="h",
        color_discrete_sequence=[couleur],
        labels={"total_beneficiaires": "Bénéficiaires", "label": ""},
    )
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
#  9. PAGE — FINANCES
# ============================================================================
def page_finances(df: pd.DataFrame):
    st.markdown("## 💰 Suivi financier")
    st.caption("Consommation budgétaire par type d'activité et par projet")

    if df.empty:
        st.info("Aucune donnée disponible.")
        return

    # KPI
    total_budget = int(df["budget"].sum())
    budget_moy = int(df["budget"].mean()) if len(df) > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Budget cumulé", f"{total_budget:,}".replace(",", " ") + " FCFA")
    c2.metric("📊 Budget moyen/activité", f"{budget_moy:,}".replace(",", " ") + " FCFA")
    c3.metric("📋 Activités avec budget", int((df["budget"] > 0).sum()))

    st.markdown("---")

    col_g, col_d = st.columns(2)

    with col_g:
        st.markdown("#### 💵 Budget par type d'activité")
        df_ag = df.groupby("type_activite")["budget"].sum().reset_index()
        df_ag["label"] = df_ag["type_activite"].map(TYPES_ACTIVITE).fillna(df_ag["type_activite"])
        fig = px.bar(
            df_ag.sort_values("budget"),
            x="budget", y="label", orientation="h",
            color_discrete_sequence=[COLORS["ACCENT"]],
            labels={"budget": "Budget (FCFA)", "label": ""},
        )
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.markdown("#### 🥧 Répartition par projet")
        df_pr = df.groupby("nom_projet")["budget"].sum().reset_index()
        df_pr["label"] = df_pr["nom_projet"].map(PROJETS).fillna(df_pr["nom_projet"])
        fig = px.pie(
            df_pr, values="budget", names="label",
            color_discrete_sequence=[COLORS["PRIMARY"], COLORS["SECONDARY"], COLORS["ACCENT"]],
            hole=0.4,
        )
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Top activités par budget
    st.markdown("#### 🏆 Top 10 activités les plus coûteuses")
    top = df.nlargest(10, "budget")[["nom_activite", "type_activite", "commune", "budget"]].copy()
    top["type_activite"] = top["type_activite"].map(TYPES_ACTIVITE).fillna(top["type_activite"])
    st.dataframe(top, use_container_width=True, hide_index=True)


# ============================================================================
#  10. PAGE — CARTOGRAPHIE
# ============================================================================
def page_cartographie(df: pd.DataFrame):
    st.markdown("## 🗺️ Cartographie des activités")
    st.caption("Localisation des activités par département et commune")

    if df.empty:
        st.info("Aucune activité à cartographier.")
        return

    # Extraire lat/lng du champ GPS (format "lat, lng")
    df_gps = df.copy()
    df_gps["lat"] = None
    df_gps["lng"] = None

    for idx, row in df_gps.iterrows():
        # 1. Essayer le champ GPS
        gps_str = str(row.get("gps", ""))
        if gps_str and "," in gps_str:
            try:
                parts = gps_str.replace(" ", "").split(",")
                lat, lng = float(parts[0]), float(parts[1])
                if lat != 0 and lng != 0:
                    df_gps.at[idx, "lat"] = lat
                    df_gps.at[idx, "lng"] = lng
                    continue
            except (ValueError, IndexError):
                pass
        # 2. Fallback : coordonnées de la commune
        commune = str(row.get("commune", "")).strip().lower()
        if commune in COMMUNES_GPS:
            df_gps.at[idx, "lat"] = COMMUNES_GPS[commune][0]
            df_gps.at[idx, "lng"] = COMMUNES_GPS[commune][1]

    df_carte = df_gps[df_gps["lat"].notna() & df_gps["lng"].notna()].copy()

    if df_carte.empty:
        st.warning(
            "Aucune coordonnée GPS exploitable. "
            "Vérifiez que les activités contiennent des coordonnées GPS "
            "ou que la commune est dans le dictionnaire de fallback."
        )
        return

    st.info(f"📍 {len(df_carte)} activité(s) géolocalisée(s) sur {len(df)} total.")

    df_carte["label"] = df_carte["type_activite"].map(TYPES_ACTIVITE).fillna(df_carte["type_activite"])
    df_carte["projet_label"] = df_carte["nom_projet"].map(PROJETS).fillna(df_carte["nom_projet"])

    fig = px.scatter_mapbox(
        df_carte,
        lat="lat", lon="lng",
        color="projet_label",
        size="total_beneficiaires",
        hover_name="nom_activite",
        hover_data={"label": True, "commune": True, "total_beneficiaires": True,
                    "lat": False, "lng": False, "projet_label": False},
        color_discrete_map={
            "EQUIFILLES (FoSIR)": COLORS["PRIMARY"],
            "SPACE TO LEAD (Plan Int.)": COLORS["SECONDARY"],
        },
        zoom=6,
        height=600,
        mapbox_style="open-street-map",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Répartition par département/commune
    col_g, col_d = st.columns(2)

    with col_g:
        st.markdown("#### 🏛️ Activités par département")
        if "departement" in df.columns:
            df_dep = df.groupby("departement").size().reset_index(name="count")
            df_dep = df_dep.sort_values("count", ascending=True)
            fig = px.bar(
                df_dep, x="count", y="departement", orientation="h",
                color_discrete_sequence=[COLORS["TERTIARY"]],
                labels={"count": "Activités", "departement": ""},
            )
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.markdown("#### 🏘️ Top 10 communes")
        if "commune" in df.columns:
            df_com = df.groupby("commune").size().reset_index(name="count")
            df_com = df_com.nlargest(10, "count").sort_values("count", ascending=True)
            fig = px.bar(
                df_com, x="count", y="commune", orientation="h",
                color_discrete_sequence=[COLORS["ACCENT"]],
                labels={"count": "Activités", "commune": ""},
            )
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)


# ============================================================================
#  11. EXPORT DES DONNÉES
# ============================================================================
def bouton_export(df: pd.DataFrame):
    """Ajoute un bouton de téléchargement CSV dans la sidebar."""
    if df.empty:
        return
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.sidebar.download_button(
        label="📥 Exporter (CSV)",
        data=csv,
        file_name=f"activites_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================================
#  12. MAIN
# ============================================================================
def main():
    # Étape 1 : authentification
    if "profil" not in st.session_state:
        afficher_login()
        return

    profil = st.session_state["profil"]
    info_profil = PROFILS[profil]

    # Sidebar : identité + déconnexion
    with st.sidebar:
        st.markdown(f"### 👤 {info_profil['nom']}")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            del st.session_state["profil"]
            st.rerun()
        st.markdown("---")

    # Étape 2 : charger les données
    df = charger_donnees(GOOGLE_SHEET_ID)

    if df.empty:
        st.warning("⚠️ Aucune donnée disponible. Vérifiez la source Google Sheets.")
        st.stop()

    # Étape 3 : filtres
    df_filtre = appliquer_filtres(df)

    # Étape 4 : bouton export
    bouton_export(df_filtre)

    # Étape 5 : sélection de page
    pages_dispo = info_profil["pages"]
    page = st.sidebar.radio("📄 Page", options=pages_dispo)

    # Étape 6 : afficher la page choisie
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, {COLORS['PRIMARY']} 0%, {COLORS['TERTIARY']} 100%);
                padding: 15px 25px; border-radius: 8px; margin-bottom: 20px;'>
        <h4 style='color: white; margin: 0;'>📊 Système S&E — Equi-Filles</h4>
        <p style='color: white; margin: 5px 0 0 0; font-size: 13px;'>
            EQUIFILLES (FoSIR) &amp; SPACE TO LEAD (Plan International Bénin)
        </p>
    </div>
    """, unsafe_allow_html=True)

    if page == "Vue d'ensemble":
        page_vue_ensemble(df_filtre)
    elif page == "Par type d'activité":
        page_par_type(df_filtre)
    elif page == "Indicateurs & Résultats":
        page_indicateurs(df_filtre)
    elif page == "Finances":
        page_finances(df_filtre)
    elif page == "Cartographie":
        page_cartographie(df_filtre)

    # Footer
    st.markdown("---")
    st.caption(
        f"🔄 Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}  ·  "
        f"Source : Google Sheets ({ONGLET_KOBO})  ·  "
        f"ONG Equi-Filles — Système S&E V6"
    )


if __name__ == "__main__":
    main()
