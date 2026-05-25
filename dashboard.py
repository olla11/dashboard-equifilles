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

page = st.sidebar.radio(
    "Choisir une page :",
    ["🏠 Vue Direction", "🎯 Vue Bailleurs", "👥 Vue Équipe", "💬 Qualitatif"],
)

st.sidebar.markdown("---")
projet = st.sidebar.selectbox(
    "Filtrer par projet :",
    ["Tous les projets", "EQUIFILLES", "SPACE TO LEAD"],
)

st.sidebar.markdown("---")
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
    kpi(c5, "AVANCEMENT MOYEN", f"{avancement:.0f}%", COULEURS["secondaire"])
    kpi(c6, "BUDGET PRÉVU (FCFA)", f"{budget_prevu:,.0f}".replace(",", " "),
        "#548235")
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
    kpi(c3, "ATTEINTE MOYENNE", f"{atteinte_moy*100:.0f}%", COULEURS["secondaire"])

    st.markdown("---")

    # --- Graphique atteinte par indicateur ---
    st.subheader("Pourcentage d'atteinte par indicateur")
    if nb_ind:
        ind_g = ind.copy()
        ind_g["Pct"] = ind_g["Pourcentage atteinte"] * 100
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
        kpi(c4, "PRÉVU TOTAL (FCFA)",
            f"{montant_prevu:,.0f}".replace(",", " "), "#548235")
        kpi(c5, "REÇU (FCFA)",
            f"{montant_recu:,.0f}".replace(",", " "), "#548235")
        reste = montant_prevu - montant_recu
        kpi(c6, "RESTE À RECEVOIR (FCFA)",
            f"{reste:,.0f}".replace(",", " "), "#ED7D31")

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
        ag["Score %"] = ag["Score consolide"] * 100
        fig = px.bar(
            ag.sort_values("Score %", ascending=True),
            x="Score %", y="Agent", orientation="h",
            color="Niveau global",
            color_discrete_map={
                "Excellent": "#385723", "Satisfaisant": "#70AD47",
                "À améliorer": "#FFD966", "Insuffisant": "#ED7D31",
                "Non évalué": "#A6A6A6",
            },
            text_auto=".0f",
        )
        fig.update_layout(height=max(350, 30 * len(ag)),
                          xaxis_title="Score consolidé (%)", yaxis_title="",
                          margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            agents[["Agent", "Total activites", "Score consolide",
                    "Activites critiques", "Activites en retard",
                    "Niveau global"]],
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
