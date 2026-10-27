from pathlib import Path

from flask import Flask, render_template, request
from rdflib import Graph

app = Flask(__name__)

FICHIER_ONTOLOGIE = Path(__file__).parent / "ontologie_exam.rdf"

g = Graph()
g.parse(str(FICHIER_ONTOLOGIE), format="xml")

REQUETE_MEDECINS = """
PREFIX h: <http://www.example.org/hopital#>
SELECT ?nom ?service ?specialite WHERE {
  ?m a h:Medecin ;
     h:nom ?nom ;
     h:travailleDans ?s ;
     h:aSpecialite ?sp .
  BIND(STRAFTER(STR(?s), "#") AS ?service)
  BIND(STRAFTER(STR(?sp), "#") AS ?specialite)
}
ORDER BY ?nom
"""

REQUETE_CONSULTATIONS = """
PREFIX h: <http://www.example.org/hopital#>
SELECT ?date ?medecin ?patient ?s ?sp WHERE {
  ?c a h:Consultation ;
     h:dateConsultation ?date ;
     h:aMedecin ?m ;
     h:aPatient ?p .
  ?m h:nom ?medecin .
  ?p h:nom ?patient .
  OPTIONAL { ?m h:travailleDans ?s . }
  OPTIONAL { ?m h:aSpecialite ?sp . }
}
ORDER BY ?date
"""


def nom_local(iri):
    """Garde ce qui suit le # dans une IRI (ou '' si absente)."""
    return str(iri).split("#")[-1] if iri is not None else ""


@app.route("/")
def accueil():
    q = request.args.get("q", "").strip().lower()
    medecins = []

    for r in g.query(REQUETE_MEDECINS):
        m = {
            "nom": str(r.nom),
            "service": str(r.service).replace("Service", ""),
            "specialite": str(r.specialite),
        }
        if (
            q in m["service"].lower()
            or q in m["specialite"].lower()
            or q in m["nom"].lower()
        ):
            medecins.append(m)

    return render_template(
        "index.html",
        medecins=medecins,
        q=q,
    )


@app.route("/consultations")
def consultations():
    q = request.args.get("q", "").strip().lower()
    date_filter = request.args.get("date", "").strip()
    toutes_les_consultations = []

    for r in g.query(REQUETE_CONSULTATIONS):
        item = {
            "date": str(r.date),
            "medecin": str(r.medecin),
            "patient": str(r.patient),
            "service": nom_local(r.s).replace("Service", ""),
            "specialite": nom_local(r.sp),
        }
        toutes_les_consultations.append(item)

    # Filtrage côté Python : simple et adapté à ce petit prototype.
    consultations_filtrees = []
    for c in toutes_les_consultations:
        texte = " ".join([
            c["date"], c["medecin"], c["patient"], c["service"], c["specialite"]
        ]).lower()
        correspond_recherche = not q or q in texte
        correspond_date = not date_filter or c["date"] == date_filter
        if correspond_recherche and correspond_date:
            consultations_filtrees.append(c)

    patients_count = len({c["patient"] for c in consultations_filtrees})
    medecins_count = len({c["medecin"] for c in consultations_filtrees})

    return render_template(
        "consultations.html",
        consultations=consultations_filtrees,
        patients_count=patients_count,
        medecins_count=medecins_count,
        q=q,
        date_filter=date_filter,
    )


if __name__ == "__main__":
    app.run(debug=True)
