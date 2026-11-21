"""Conservative, auditable country mentions from ORIGINAL publication titles.

This is an association index, not event location, actor nationality or attribution.
Publisher location, web host, FARA registrant name, and CISA product name are
never used as evidence of which country an incident belongs to.
"""
from __future__ import annotations

import re

# Exact or unambiguous adjectival country names. Deliberately exclude stand-alone
# "Korea", "Georgia", "Guinea", "US" without punctuation, and short ISO codes.
# Each hit means only "the title references this country".
COUNTRY_TERMS: dict[str, tuple[str, ...]] = {
    "US": ("United States", "United States of America", "USA", "U.S.", "U.S"),
    "GB": ("United Kingdom", "Britain", "British", "UK"),
    "RU": ("Russia", "Russian", "Russian Federation"),
    "UA": ("Ukraine", "Ukrainian"),
    "CN": ("China", "Chinese", "People's Republic of China", "PRC"),
    "TW": ("Taiwan", "Taiwanese"),
    "KP": ("North Korea", "North Korean", "DPRK", "Democratic People's Republic of Korea"),
    "KR": ("South Korea", "South Korean", "Republic of Korea"),
    "IR": ("Iran", "Iranian"),
    "IQ": ("Iraq", "Iraqi"),
    "IL": ("Israel", "Israeli"),
    "PS": ("Palestine", "Palestinian", "Palestinian territories"),
    "SY": ("Syria", "Syrian"),
    "LB": ("Lebanon", "Lebanese"),
    "YE": ("Yemen", "Yemeni"),
    "SA": ("Saudi Arabia", "Saudi"),
    "AE": ("United Arab Emirates", "Emirati", "UAE"),
    "TR": ("Türkiye", "Turkey", "Turkish"),
    "AF": ("Afghanistan", "Afghan"),
    "PK": ("Pakistan", "Pakistani"),
    "IN": ("India", "Indian"),
    "JP": ("Japan", "Japanese"),
    "VN": ("Vietnam", "Vietnamese"),
    "PH": ("Philippines", "Philippine", "Filipino"),
    "ID": ("Indonesia", "Indonesian"),
    "MY": ("Malaysia", "Malaysian"),
    "SG": ("Singapore", "Singaporean"),
    "TH": ("Thailand", "Thai"),
    "MM": ("Myanmar", "Burma", "Burmese"),
    "KH": ("Cambodia", "Cambodian"),
    "LA": ("Laos", "Lao"),
    "BD": ("Bangladesh", "Bangladeshi"),
    "LK": ("Sri Lanka", "Sri Lankan"),
    "NP": ("Nepal", "Nepalese"),
    "AU": ("Australia", "Australian"),
    "NZ": ("New Zealand",),
    "CA": ("Canada", "Canadian"),
    "MX": ("Mexico", "Mexican"),
    "BR": ("Brazil", "Brazilian"),
    "AR": ("Argentina", "Argentine", "Argentinian"),
    "CL": ("Chile", "Chilean"),
    "CO": ("Colombia", "Colombian"),
    "PE": ("Peru", "Peruvian"),
    "VE": ("Venezuela", "Venezuelan"),
    "CU": ("Cuba", "Cuban"),
    "HT": ("Haiti", "Haitian"),
    "DO": ("Dominican Republic", "Dominican"),
    "PA": ("Panama", "Panamanian"),
    "NI": ("Nicaragua", "Nicaraguan"),
    "GT": ("Guatemala", "Guatemalan"),
    "SV": ("El Salvador", "Salvadoran"),
    "HN": ("Honduras", "Honduran"),
    "CR": ("Costa Rica", "Costa Rican"),
    "EC": ("Ecuador", "Ecuadorian"),
    "BO": ("Bolivia", "Bolivian"),
    "PY": ("Paraguay", "Paraguayan"),
    "UY": ("Uruguay", "Uruguayan"),
    "PL": ("Poland", "Polish"),
    "DE": ("Germany", "German"),
    "FR": ("France", "French"),
    "IT": ("Italy", "Italian"),
    "ES": ("Spain", "Spanish"),
    "PT": ("Portugal", "Portuguese"),
    "NL": ("Netherlands", "Dutch"),
    "BE": ("Belgium", "Belgian"),
    "CH": ("Switzerland", "Swiss"),
    "AT": ("Austria", "Austrian"),
    "SE": ("Sweden", "Swedish"),
    "NO": ("Norway", "Norwegian"),
    "FI": ("Finland", "Finnish"),
    "DK": ("Denmark", "Danish"),
    "IS": ("Iceland", "Icelandic"),
    "IE": ("Ireland", "Irish"),
    "CZ": ("Czech Republic", "Czechia", "Czech"),
    "SK": ("Slovakia", "Slovak"),
    "HU": ("Hungary", "Hungarian"),
    "RO": ("Romania", "Romanian"),
    "BG": ("Bulgaria", "Bulgarian"),
    "GR": ("Greece", "Greek"),
    "CY": ("Cyprus", "Cypriot"),
    "RS": ("Serbia", "Serbian"),
    "BA": ("Bosnia and Herzegovina", "Bosnian"),
    "HR": ("Croatia", "Croatian"),
    "SI": ("Slovenia", "Slovenian"),
    "ME": ("Montenegro", "Montenegrin"),
    "MK": ("North Macedonia", "Macedonian"),
    "AL": ("Albania", "Albanian"),
    "XK": ("Kosovo", "Kosovar"),
    "BY": ("Belarus", "Belarusian"),
    "MD": ("Moldova", "Moldovan"),
    "GE": ("Republic of Georgia", "Georgian"),
    "AM": ("Armenia", "Armenian"),
    "AZ": ("Azerbaijan", "Azerbaijani"),
    "KZ": ("Kazakhstan", "Kazakh"),
    "KG": ("Kyrgyzstan", "Kyrgyz"),
    "TJ": ("Tajikistan", "Tajik"),
    "UZ": ("Uzbekistan", "Uzbek"),
    "TM": ("Turkmenistan", "Turkmen"),
    "EG": ("Egypt", "Egyptian"),
    "LY": ("Libya", "Libyan"),
    "TN": ("Tunisia", "Tunisian"),
    "DZ": ("Algeria", "Algerian"),
    "MA": ("Morocco", "Moroccan"),
    "SD": ("Sudan", "Sudanese"),
    "SS": ("South Sudan"),
    "ET": ("Ethiopia", "Ethiopian"),
    "SO": ("Somalia", "Somali"),
    "KE": ("Kenya", "Kenyan"),
    "UG": ("Uganda", "Ugandan"),
    "TZ": ("Tanzania", "Tanzanian"),
    "RW": ("Rwanda", "Rwandan"),
    "CD": ("Democratic Republic of the Congo", "DR Congo", "DRC", "Congolese"),
    "CG": ("Republic of the Congo", "Congo-Brazzaville"),
    "NG": ("Nigeria", "Nigerian"),
    "NE": ("Niger", "Nigerien"),
    "GH": ("Ghana", "Ghanaian"),
    "CI": ("Côte d'Ivoire", "Ivory Coast", "Ivorian"),
    "SN": ("Senegal", "Senegalese"),
    "ML": ("Mali", "Malian"),
    "BF": ("Burkina Faso", "Burkinabè"),
    "ZA": ("South Africa", "South African"),
    "ZW": ("Zimbabwe", "Zimbabwean"),
    "ZM": ("Zambia", "Zambian"),
    "MZ": ("Mozambique", "Mozambican"),
    "AO": ("Angola", "Angolan"),
    "CM": ("Cameroon", "Cameroonian"),
    "MG": ("Madagascar", "Malagasy"),
}

# Place-to-country mapping is weaker: a place reference is a geographically
# associated lead, NOT proof of event location or the actor's nationality.
PLACE_TERMS: dict[str, tuple[str, ...]] = {
    "US": ("Hawaii", "Alaska", "Washington, D.C.", "New York City"),
    "RU": ("Moscow", "St. Petersburg"),
    "UA": ("Kyiv", "Kiev"),
    "CN": ("Beijing", "Shanghai"),
    "TW": ("Taipei"),
    "KP": ("Pyongyang"),
    "KR": ("Seoul"),
    "IR": ("Tehran"),
    "CU": ("Havana"),
    "GB": ("London"),
    "FR": ("Paris"),
    "PL": ("Warsaw"),
    "IL": ("Jerusalem", "Tel Aviv"),
    "LB": ("Beirut"),
    "SY": ("Damascus"),
}

# These acronyms have unrelated everyday meanings or appear in product names.
CASE_SENSITIVE = {"UK", "USA", "U.S.", "U.S", "PRC", "DPRK", "UAE", "DRC"}
SKIP_SOURCE_IDS = {"fara", "cisa"}
PATTERNS = [
    (code, term, basis, re.compile(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])",
        0 if term in CASE_SENSITIVE else re.IGNORECASE))
    for basis, mapping in (("title-country-name", COUNTRY_TERMS), ("title-place-name", PLACE_TERMS))
    for code, terms in mapping.items() for term in terms
]


def infer_country_mentions(record: dict) -> list[dict]:
    """Separate transparent title mentions from publisher-supplied countries.

    FARA registrant names and CISA product labels do not identify an operating
    country or foreign principal. Never guess from those fields. No network or AI.
    """
    if str(record.get("sourceId", "")).lower() in SKIP_SOURCE_IDS:
        return []
    title = str(record.get("title") or "")
    if not title:
        return []
    # A few geographic adjectives commonly mean a *region*, not a country.
    filtered = re.sub(r"\bIndian Ocean\b", "", title, flags=re.IGNORECASE)
    detected: dict[str, dict] = {}
    for code, term, basis, pattern in PATTERNS:
        for match in pattern.finditer(filtered):
            hit = match.group(0)
            entry = {
                "code": code,
                "basis": basis,
                "matchedText": hit,
                "confidence": "high" if basis == "title-country-name" else "medium",
            }
            previous = detected.get(code)
            if previous is None or (previous["basis"] == "title-place-name" and basis == "title-country-name"):
                detected[code] = entry
            break
    return [detected[c] for c in sorted(detected)]
