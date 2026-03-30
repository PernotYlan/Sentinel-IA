def generate_report(target, scan, analysis):

    report = f"""
==============================
RAPPORT CYBERSECURITE
==============================

Cible : {target}

------------------------------
RESULTAT DU SCAN
------------------------------

{scan}

------------------------------
ANALYSE IA
------------------------------

{analysis}

==============================
FIN DU RAPPORT
==============================
"""

    return report