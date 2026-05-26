# -*- coding: utf-8 -*-
"""
============================================================================
 TABLEAU DE BORD — SUIVI-ÉVALUATION  |  ONG EQUI-FILLES
 Projets EQUIFILLES (FoSIR) & SPACE TO LEAD (Plan International Bénin)
----------------------------------------------------------------------------
 Application Streamlit qui lit les 5 onglets sources du fichier
 « Outil de pilotage V5 » et affiche un tableau de bord complet en 4 pages.

 ─── INSTALLATION (à faire une seule fois) ─────────────────────────────────
 1. Installer Python 3.9 ou plus récent.
 2. Dans un terminal, installer les librairies nécessaires :
        pip install streamlit pandas plotly openpyxl
 3. Placer ce fichier (dashboard.py) dans un dossier.
 4. Mettre le fichier Excel V5 dans le MÊME dossier, nommé :
        Outil_Pilotage_SE_EquiFilles_v5.xlsx
    (ou ajuster la variable CHEMIN_FICHIER ci-dessous)

 ─── LANCEMENT ─────────────────────────────────────────────────────────────
 Dans le terminal, depuis le dossier :
        streamlit run dashboard.py
 Le tableau de bord s'ouvre dans le navigateur.

 ─── HÉBERGEMENT EN LIGNE (gratuit) ────────────────────────────────────────
 1. Créer un compte sur https://streamlit.io  (Streamlit Community Cloud).
 2. Déposer dashboard.py + le fichier Excel dans un dépôt GitHub.
 3. Connecter le dépôt à Streamlit Cloud : l'application devient accessible
    par un lien partageable.
============================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
#  CONFIGURATION
# ============================================================================
# --- SOURCE DES DONNÉES ----------------------------------------------------
# Deux modes possibles :
#
#  MODE 1 — Fichier Excel local (par défaut) :
#     Laisser GOOGLE_SHEET_ID vide ("").
#     Le dashboard lit le fichier .xlsx placé dans le même dossier.
#
#  MODE 2 — Google Sheets en ligne (données toujours à jour) :
#     1. Importer le fichier V5 dans Google Drive et l'ouvrir en Google Sheets.
#     2. Menu Fichier > Partager > Publier sur le web > Publier.
#     3. Copier l'identifiant du classeur depuis l'URL :
#        https://docs.google.com/spreadsheets/d/IDENTIFIANT_ICI/edit
#     4. Coller cet identifiant entre les guillemets de GOOGLE_SHEET_ID.
#     Dès que GOOGLE_SHEET_ID est renseigné, le dashboard lit Google Sheets.
# ---------------------------------------------------------------------------
GOOGLE_SHEET_ID = "1y9MpwI9AQcz21KZNHJOq7j3u7Zff9lXnto_bXBxe8nk"   # <-- coller ici l'identifiant du Google Sheets (MODE 2)

CHEMIN_FICHIER = "Outil_Pilotage_SE_EquiFilles_v5.xlsx"  # utilisé en MODE 1

# Noms exacts des onglets sources (identiques en Excel et en Google Sheets)
ONGLET_ACTIVITES   = "LK. Source Looker"
ONGLET_INDICATEURS = "LK2. Source Indicateurs"
ONGLET_AGENTS      = "LK3. Source Agents"
ONGLET_FINANCIER   = "LK4. Source Financier"
ONGLET_QUALITATIF  = "LK5. Source Qualitatif"

# Palette de couleurs (cohérente avec le fichier Excel)
COULEURS = {
    "EQUIFILLES": "#C00000",
    "SPACE TO LEAD": "#00B050",
    "primaire": "#1F3864",
    "secondaire": "#2E75B6",
}
# Couleur par statut d'activité
COULEUR_STATUT = {
    "À temps": "#70AD47",
    "À surveiller": "#FFD966",
    "En retard": "#ED7D31",
    "Critique": "#C00000",
    "Terminé à temps": "#385723",
    "Terminé hors délai": "#BF6312",
    "Non réalisé": "#404040",
    "En attente": "#A6A6A6",
}

st.set_page_config(
    page_title="Pilotage S&E — Equi-Filles",
    page_icon="📊",
    layout="wide",
)


# ============================================================================
#  COMPTES ET ACCÈS  —  MODIFIER LES MOTS DE PASSE ICI
# ============================================================================
# Pour changer un mot de passe : remplacer la valeur "mot_de_passe" ci-dessous.
# Pour chaque profil, "pages" liste les pages auxquelles il a accès.
COMPTES = {
    "direction": {
        "mot_de_passe": "direction2026",
        "libelle": "Direction",
        "pages": ["🏠 Vue Direction", "🎯 Vue Bailleurs",
                  "👥 Vue Équipe", "💬 Qualitatif"],
    },
    "bailleur": {
        "mot_de_passe": "bailleur2026",
        "libelle": "Bailleur",
        "pages": ["🏠 Vue Direction", "🎯 Vue Bailleurs"],
    },
    "equipe": {
        "mot_de_passe": "equipe2026",
        "libelle": "Equipe",
        "pages": ["🏠 Vue Direction", "👥 Vue Équipe"],
    },
}


def page_connexion():
    """Affiche la page de connexion et vérifie les identifiants."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_g, col_c, col_d = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            "<h2 style='text-align:center;color:#1F3864;'>"
            "📊 Tableau de bord Suivi-Évaluation</h2>",
            unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:#595959;'>"
            "ONG Equi-Filles — Connexion requise</p>",
            unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        identifiant = st.text_input("Identifiant")
        mot_de_passe = st.text_input("Mot de passe", type="password")

        if st.button("Se connecter", use_container_width=True):
            ident = identifiant.strip().lower()
            compte = COMPTES.get(ident)
            if compte and mot_de_passe == compte["mot_de_passe"]:
                st.session_state["connecte"] = True
                st.session_state["profil"] = ident
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Accès réservé aux personnes autorisées de l'ONG "
                   "Equi-Filles et à ses partenaires.")


# --- Contrôle d'accès : bloque le dashboard tant que non connecté ----------
if not st.session_state.get("connecte", False):
    page_connexion()
    st.stop()

# Profil de l'utilisateur connecté
PROFIL = st.session_state.get("profil", "")
PROFIL_INFO = COMPTES.get(PROFIL, {})
PAGES_AUTORISEES = PROFIL_INFO.get("pages", ["🏠 Vue Direction"])


# ============================================================================
#  CHARGEMENT DES DONNÉES
# ============================================================================
def _lire_onglet(nom_onglet):
    """Lit un onglet, depuis Google Sheets si GOOGLE_SHEET_ID est renseigné,
    sinon depuis le fichier Excel local."""
    if GOOGLE_SHEET_ID:
        # Lecture en ligne via l'export CSV de Google Sheets.
        import urllib.parse
        onglet_encode = urllib.parse.quote(nom_onglet)
        url = (f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
               f"/gviz/tq?tqx=out:csv&sheet={onglet_encode}")
        return pd.read_csv(url)
    else:
        # Lecture locale du fichier Excel.
        return pd.read_excel(CHEMIN_FICHIER, sheet_name=nom_onglet)


@st.cache_data(ttl=600)  # mise en cache 10 minutes
def charger_donnees():
    """Lit les 5 onglets sources (Excel local ou Google Sheets) et renvoie
    5 DataFrames."""
    try:
        activites = _lire_onglet(ONGLET_ACTIVITES)
        indicateurs = _lire_onglet(ONGLET_INDICATEURS)
        agents = _lire_onglet(ONGLET_AGENTS)
        financier = _lire_onglet(ONGLET_FINANCIER)
        qualitatif = _lire_onglet(ONGLET_QUALITATIF)
    except FileNotFoundError:
        st.error(f"Fichier introuvable : {CHEMIN_FICHIER}. "
                 f"Placez le fichier Excel dans le même dossier que ce script, "
                 f"ou renseignez GOOGLE_SHEET_ID pour lire Google Sheets.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur de lecture des données : {e}")
        st.stop()

    # Nettoyage : retirer les lignes vides (sans projet/agent/type)
    activites = activites.dropna(subset=["Projet"])
    activites = activites[activites["Projet"].astype(str).str.strip() != ""]
    # Exclure les lignes de total recopiées des Gantt
    activites = activites[activites["Code activite"].astype(str).str.upper()
                          != "TOTAL"]
    activites = activites[activites["Code activite"].astype(str).str.strip()
                          != ""]
    indicateurs = indicateurs.dropna(subset=["Projet"])
    indicateurs = indicateurs[indicateurs["Projet"].astype(str).str.strip() != ""]
    agents = agents.dropna(subset=["Agent"])
    agents = agents[agents["Agent"].astype(str).str.strip() != ""]
    financier = financier.dropna(subset=["Projet"])
    financier = financier[financier["Projet"].astype(str).str.strip() != ""]
    if not qualitatif.empty and "Type de fiche" in qualitatif.columns:
        qualitatif = qualitatif.dropna(subset=["Type de fiche"])
        qualitatif = qualitatif[qualitatif["Type de fiche"].astype(str).str.strip() != ""]

    # --- Conversion des colonnes numériques ---------------------------------
    # Quand les données viennent de Google Sheets, les nombres peuvent être lus
    # comme du texte (espaces, formats). On les force en numérique ici.
    def num(df, colonnes):
        for c in colonnes:
            if c in df.columns:
                # Retire espaces insécables et espaces, remplace virgule décimale
                serie = (df[c].astype(str)
                         .str.replace("\u202f", "", regex=False)
                         .str.replace("\xa0", "", regex=False)
                         .str.replace(" ", "", regex=False)
                         .str.replace(",", ".", regex=False))
                df[c] = pd.to_numeric(serie, errors="coerce").fillna(0)
        return df

    activites = num(activites, ["Pourcentage prevu", "Pourcentage reel",
                                "Budget prevu", "Budget consomme",
                                "Criticite", "Note", "Quantite cible",
                                "Quantite realisee"])
    indicateurs = num(indicateurs, ["Cible", "Valeur cumulee",
                                    "Pourcentage atteinte"])
    agents = num(agents, ["Total activites", "Activites EQUIFILLES",
                          "Activites S2L", "Score consolide",
                          "Activites critiques", "Activites en retard",
                          "Activites terminees"])
    financier = num(financier, ["Montant prevu", "Montant recu"])

    return activites, indicateurs, agents, financier, qualitatif


# ============================================================================
#  FONCTIONS UTILITAIRES D'AFFICHAGE
# ============================================================================
def kpi(colonne, libelle, valeur, couleur="#1F3864"):
    """Affiche un indicateur clé dans une colonne."""
    colonne.markdown(
        f"""
        <div style="background:#F2F2F2;border-radius:8px;padding:14px;
                    text-align:center;border-top:4px solid {couleur};">
            <div style="font-size:13px;color:#595959;font-weight:600;">{libelle}</div>
            <div style="font-size:30px;color:{couleur};font-weight:800;">{valeur}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def fmt_fcfa(valeur):
    """Formate un montant en FCFA, de façon sûre même si la valeur est du texte."""
    try:
        return f"{float(valeur):,.0f}".replace(",", " ")
    except (ValueError, TypeError):
        return "0"


def fmt_pct(valeur):
    """Formate un pourcentage. Accepte une fraction (0-1) ou un nombre (0-100)."""
    try:
        v = float(valeur)
    except (ValueError, TypeError):
        return "0%"
    # Si la valeur est une fraction (<= 1.5), la convertir en pourcentage.
    if abs(v) <= 1.5:
        v = v * 100
    return f"{v:.0f}%"


def en_pourcentage(serie):
    """Convertit une colonne en pourcentage 0-100, qu'elle soit en fraction ou non."""
    s = pd.to_numeric(serie, errors="coerce").fillna(0)
    # Si le maximum est <= 1.5, les valeurs sont des fractions -> x100
    if len(s) > 0 and s.max() <= 1.5:
        s = s * 100
    return s


def filtrer_projet(df, projet_choisi, colonne="Projet"):
    """Filtre un DataFrame selon le projet sélectionné."""
    if projet_choisi == "Tous les projets":
        return df
    return df[df[colonne] == projet_choisi]


# ============================================================================
#  CHARGEMENT
# ============================================================================
activites, indicateurs, agents, financier, qualitatif = charger_donnees()


# ============================================================================
#  BARRE LATÉRALE — NAVIGATION ET FILTRES
# ============================================================================
st.sidebar.image(
    "https://via.placeholder.com/200x70/1F3864/FFFFFF?text=Equi-Filles",
    use_container_width=True,
)
st.sidebar.title("Navigation")
st.sidebar.caption(f"Connecté : **{PROFIL_INFO.get('libelle', '')}**")

page = st.sidebar.radio(
    "Choisir une page :",
    PAGES_AUTORISEES,
)

st.sidebar.markdown("---")
projet = st.sidebar.selectbox(
    "Filtrer par projet :",
    ["Tous les projets", "EQUIFILLES", "SPACE TO LEAD"],
)

st.sidebar.markdown("---")
if st.sidebar.button("🔓 Se déconnecter", use_container_width=True):
    st.session_state["connecte"] = False
    st.session_state["profil"] = ""
    st.rerun()

st.sidebar.caption(
    "Données issues du fichier de pilotage V5. "
    "Pour rafraîchir, rechargez la page (les données sont mises en cache 10 min)."
)
if st.sidebar.button("🔄 Recharger les données"):
    st.cache_data.clear()
    st.rerun()


# ============================================================================
#  PAGE 1 — VUE DIRECTION
# ============================================================================
# Garde de sécurité : vérifie que la page demandée est bien autorisée
if page not in PAGES_AUTORISEES:
    st.error("Vous n'avez pas accès à cette page.")
    st.stop()

if page == "🏠 Vue Direction":
    st.title("🏠 Vue Direction — Tableau de bord général")
    st.caption(f"Projet sélectionné : **{projet}**")

    act = filtrer_projet(activites, projet)

    # --- Indicateurs clés ---
    nb_activites = len(act)
    nb_terminees = len(act[act["Statut"].isin(
        ["Terminé à temps", "Terminé hors délai"])])
    nb_retard = len(act[act["Statut"] == "En retard"])
    nb_critique = len(act[act["Statut"] == "Critique"])
    avancement = act["Pourcentage reel"].mean() if nb_activites else 0
    budget_prevu = act["Budget prevu"].sum()
    budget_conso = act["Budget consomme"].sum()

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "ACTIVITÉS PLANIFIÉES", nb_activites, COULEURS["primaire"])
    kpi(c2, "ACTIVITÉS TERMINÉES", nb_terminees, "#385723")
    kpi(c3, "EN RETARD", nb_retard, "#ED7D31")
    kpi(c4, "CRITIQUES", nb_critique, "#C00000")

    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7 = st.columns(3)
    kpi(c5, "AVANCEMENT MOYEN", fmt_pct(avancement), COULEURS["secondaire"])
    kpi(c6, "BUDGET PRÉVU (FCFA)", fmt_fcfa(budget_prevu), "#548235")
    taux_conso = (budget_conso / budget_prevu * 100) if budget_prevu else 0
    kpi(c7, "TAUX DE CONSOMMATION", f"{taux_conso:.1f}%", "#548235")

    st.markdown("---")

    col_g, col_d = st.columns(2)

    # --- Graphique répartition par statut ---
    with col_g:
        st.subheader("Répartition des activités par statut")
        if nb_activites:
            rep = act["Statut"].value_counts().reset_index()
            rep.columns = ["Statut", "Nombre"]
            fig = px.pie(
                rep, names="Statut", values="Nombre", hole=0.45,
                color="Statut", color_discrete_map=COULEUR_STATUT,
            )
            fig.update_traces(textposition="outside", textinfo="label+value")
            fig.update_layout(showlegend=False, height=380,
                              margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune activité à afficher.")

    # --- Graphique avancement par projet ---
    with col_d:
        st.subheader("Avancement moyen par projet")
        avp = activites.groupby("Projet")["Pourcentage reel"].mean().reset_index()
        fig2 = px.bar(
            avp, x="Projet", y="Pourcentage reel", color="Projet",
            color_discrete_map=COULEURS, text_auto=".0f",
        )
        fig2.update_layout(showlegend=False, height=380,
                           yaxis_title="Avancement (%)",
                           margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig2, use_container_width=True)

    # --- Tableau de synthèse ---
    st.subheader("Synthèse des activités")
    colonnes_aff = ["Projet", "Code activite", "Activite", "Responsable",
                    "Statut", "Pourcentage reel"]
    st.dataframe(
        act[colonnes_aff].rename(columns={"Pourcentage reel": "% réel"}),
        use_container_width=True, hide_index=True,
    )


# ============================================================================
#  PAGE 2 — VUE BAILLEURS
# ============================================================================
elif page == "🎯 Vue Bailleurs":
    st.title("🎯 Vue Bailleurs — Résultats et financement")
    st.caption(f"Projet sélectionné : **{projet}**")

    ind = filtrer_projet(indicateurs, projet)
    fin = filtrer_projet(financier, projet)

    # --- Indicateurs de résultats ---
    st.subheader("Indicateurs de résultats")
    nb_ind = len(ind)
    nb_atteints = len(ind[ind["Statut"] == "Atteint"])
    atteinte_moy = ind["Pourcentage atteinte"].mean() if nb_ind else 0

    c1, c2, c3 = st.columns(3)
    kpi(c1, "INDICATEURS SUIVIS", nb_ind, COULEURS["primaire"])
    kpi(c2, "INDICATEURS ATTEINTS", nb_atteints, "#385723")
    kpi(c3, "ATTEINTE MOYENNE", fmt_pct(atteinte_moy), COULEURS["secondaire"])

    st.markdown("---")

    # --- Graphique atteinte par indicateur ---
    st.subheader("Pourcentage d'atteinte par indicateur")
    if nb_ind:
        ind_g = ind.copy()
        ind_g["Pct"] = en_pourcentage(ind_g["Pourcentage atteinte"])
        fig = px.bar(
            ind_g, x="Pct", y="Code", orientation="h",
            color="Projet", color_discrete_map=COULEURS,
            text_auto=".0f", hover_data=["Indicateur"],
        )
        fig.update_layout(
            height=max(400, 22 * nb_ind), xaxis_title="Atteinte (%)",
            yaxis_title="", margin=dict(t=20, b=20, l=20, r=20),
        )
        fig.add_vline(x=100, line_dash="dash", line_color="green")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun indicateur à afficher.")

    # --- Tableau des indicateurs ---
    st.dataframe(
        ind[["Projet", "Code", "Indicateur", "Cible",
             "Valeur cumulee", "Pourcentage atteinte", "Statut"]],
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")

    # --- Suivi financier (décaissements) ---
    st.subheader("Décaissements des bailleurs")
    if not fin.empty:
        montant_prevu = fin["Montant prevu"].sum()
        montant_recu = fin["Montant recu"].sum()
        c4, c5, c6 = st.columns(3)
        kpi(c4, "PRÉVU TOTAL (FCFA)", fmt_fcfa(montant_prevu), "#548235")
        kpi(c5, "REÇU (FCFA)", fmt_fcfa(montant_recu), "#548235")
        reste = montant_prevu - montant_recu
        kpi(c6, "RESTE À RECEVOIR (FCFA)", fmt_fcfa(reste), "#ED7D31")

        fig_f = px.bar(
            fin, x="Tranche", y=["Montant prevu", "Montant recu"],
            barmode="group", color_discrete_sequence=["#A6A6A6", "#548235"],
        )
        fig_f.update_layout(height=350, yaxis_title="FCFA",
                            margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_f, use_container_width=True)

        st.dataframe(fin, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée de décaissement.")


# ============================================================================
#  PAGE 3 — VUE ÉQUIPE
# ============================================================================
elif page == "👥 Vue Équipe":
    st.title("👥 Vue Équipe — Suivi opérationnel")
    st.caption(f"Projet sélectionné : **{projet}**")

    act = filtrer_projet(activites, projet)

    # --- Performance des agents ---
    st.subheader("Performance des agents")
    if not agents.empty:
        ag = agents.copy()
        # Score converti en pourcentage de façon sûre (fraction 0-1 ou déjà 0-100)
        ag["Score %"] = en_pourcentage(ag["Score consolide"])
        ag = ag.sort_values("Score %", ascending=True)

        # Indicateurs de synthèse au-dessus du graphique
        nb_agents = len(ag)
        score_moyen = ag["Score %"].mean() if nb_agents else 0
        nb_excellent = len(ag[ag["Niveau global"] == "Excellent"])
        s1, s2, s3 = st.columns(3)
        kpi(s1, "AGENTS ÉVALUÉS", nb_agents, COULEURS["primaire"])
        kpi(s2, "SCORE MOYEN", f"{score_moyen:.0f}%", COULEURS["secondaire"])
        kpi(s3, "NIVEAU EXCELLENT", nb_excellent, "#385723")
        st.markdown("<br>", unsafe_allow_html=True)

        fig = px.bar(
            ag, x="Score %", y="Agent", orientation="h",
            color="Niveau global",
            color_discrete_map={
                "Excellent": "#385723", "Satisfaisant": "#70AD47",
                "À améliorer": "#FFD966", "Insuffisant": "#ED7D31",
                "Non évalué": "#A6A6A6",
            },
            text="Score %",
        )
        # Barres lisibles : hauteur fixe par agent, étiquettes nettes
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside",
                          cliponaxis=False)
        fig.update_layout(
            height=max(300, 42 * len(ag)),
            xaxis_title="Score consolidé (%)", yaxis_title="",
            xaxis=dict(range=[0, 110]),
            margin=dict(t=10, b=10, l=10, r=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="left", x=0),
            bargap=0.25,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tableau détaillé avec score en pourcentage lisible
        ag_tab = ag.copy()
        ag_tab["Score"] = ag_tab["Score %"].round(0).astype(int).astype(str) + " %"
        st.dataframe(
            ag_tab[["Agent", "Total activites", "Score",
                    "Activites critiques", "Activites en retard",
                    "Activites terminees", "Niveau global"]]
            .rename(columns={
                "Total activites": "Total activités",
                "Activites critiques": "Critiques",
                "Activites en retard": "En retard",
                "Activites terminees": "Terminées",
                "Niveau global": "Niveau"}),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Aucun agent renseigné.")

    st.markdown("---")

    # --- Activités à risque ---
    st.subheader("⚠️ Activités critiques et en retard")
    a_risque = act[act["Statut"].isin(["Critique", "En retard"])]
    if not a_risque.empty:
        st.dataframe(
            a_risque[["Projet", "Code activite", "Activite", "Responsable",
                      "Date fin prevue", "Statut", "Pourcentage reel"]]
            .rename(columns={"Pourcentage reel": "% réel"}),
            use_container_width=True, hide_index=True,
        )
    else:
        st.success("Aucune activité critique ou en retard. 👍")

    # --- Activités détaillées ---
    st.subheader("Toutes les activités")
    resp_liste = ["Tous"] + sorted(
        act["Responsable"].dropna().unique().tolist())
    resp_choisi = st.selectbox("Filtrer par responsable :", resp_liste)
    act_aff = act if resp_choisi == "Tous" else act[
        act["Responsable"] == resp_choisi]
    st.dataframe(
        act_aff[["Code activite", "Activite", "Responsable", "Criticite",
                 "Statut", "Pourcentage prevu", "Pourcentage reel"]],
        use_container_width=True, hide_index=True,
    )


# ============================================================================
#  PAGE 4 — QUALITATIF
# ============================================================================
elif page == "💬 Qualitatif":
    st.title("💬 Qualitatif — Témoignages et incidents")
    st.warning(
        "⚠️ Cette page contient des données sensibles. "
        "Son accès doit être restreint à la direction et à l'agent S&E.")

    if qualitatif.empty or "Type de fiche" not in qualitatif.columns:
        st.info("Aucune donnée qualitative pour l'instant. "
                "Cette page se remplira dès que des fiches F8 seront collectées.")
    else:
        temoignages = qualitatif[qualitatif["Type de fiche"] == "Témoignage"]
        incidents = qualitatif[qualitatif["Type de fiche"] == "Incident"]

        c1, c2, c3 = st.columns(3)
        kpi(c1, "TÉMOIGNAGES", len(temoignages), "#70AD47")
        kpi(c2, "INCIDENTS", len(incidents), "#C00000")
        a_traiter = len(incidents[incidents["Statut incident"] == "À traiter"]) \
            if "Statut incident" in incidents.columns else 0
        kpi(c3, "INCIDENTS À TRAITER", a_traiter, "#ED7D31")

        st.markdown("---")

        # --- Témoignages ---
        st.subheader("Témoignages / histoires de changement")
        if not temoignages.empty:
            # Répartition par domaine
            if "Domaine" in temoignages.columns:
                dom = temoignages["Domaine"].value_counts().reset_index()
                dom.columns = ["Domaine", "Nombre"]
                fig = px.bar(dom, x="Domaine", y="Nombre",
                             color_discrete_sequence=["#70AD47"])
                fig.update_layout(height=300,
                                  margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            # Liste des témoignages
            for _, t in temoignages.iterrows():
                with st.expander(
                        f"📖 {t.get('Domaine', 'Témoignage')} — "
                        f"{t.get('Commune/Site', '')}"):
                    st.write(t.get("Recit/Description", ""))
                    cit = t.get("Citation", "")
                    if cit and str(cit).strip():
                        st.markdown(f"> *« {cit} »*")
        else:
            st.info("Aucun témoignage enregistré.")

        st.markdown("---")

        # --- Incidents ---
        st.subheader("Suivi des incidents")
        if not incidents.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                if "Gravite" in incidents.columns:
                    grav = incidents["Gravite"].value_counts().reset_index()
                    grav.columns = ["Gravité", "Nombre"]
                    fig = px.pie(grav, names="Gravité", values="Nombre",
                                 hole=0.4,
                                 color_discrete_sequence=["#FFD966",
                                                          "#ED7D31",
                                                          "#C00000"])
                    fig.update_layout(height=300,
                                      margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
            with col_b:
                if "Statut incident" in incidents.columns:
                    stt = incidents["Statut incident"].value_counts().reset_index()
                    stt.columns = ["Statut", "Nombre"]
                    fig = px.bar(stt, x="Statut", y="Nombre",
                                 color_discrete_sequence=["#2E75B6"])
                    fig.update_layout(height=300,
                                      margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
            # Tableau (sans le détail nominatif)
            cols_inc = [c for c in ["Date", "Commune/Site", "Gravite",
                                    "Statut incident", "Structure reference"]
                        if c in incidents.columns]
            st.dataframe(incidents[cols_inc], use_container_width=True,
                         hide_index=True)
        else:
            st.success("Aucun incident signalé.")


# ============================================================================
#  PIED DE PAGE
# ============================================================================
st.markdown("---")
st.caption(
    "Tableau de bord Suivi-Évaluation — ONG Equi-Filles | "
    "Projets EQUIFILLES & SPACE TO LEAD | "
    "Données : Outil de pilotage V5"
)
