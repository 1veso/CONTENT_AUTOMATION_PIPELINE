"""
One-shot script to create the 30-day Provinzial Instagram calendar in Airtable.

- Start: 2026-06-01 (Mon), post time 10:00, Europe/Berlin (CEST = +02:00)
- 30 records, one per day, ending 2026-06-30 (Tue)
- 9:16 prompts, brand-voice German captions, all 5 pillars rotated
- Reference Images attachment populated with the 3 brand reference URLs already on fal.media
"""
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, ".")
from tools.airtable import create_records_batch, get_next_index

# CEST = UTC+2 (June is summer time in Europe/Berlin)
CEST = timezone(timedelta(hours=2))
START = datetime(2026, 6, 1, 10, 0, 0, tzinfo=CEST)

# Use the 3 most representative reference URLs (logo, branding kit, design richtlinien)
# attached to every record so the agent + Nano Banana can see them at gen time.
REF_URLS = [
    "https://v3b.fal.media/files/b/0a99f0c8/XdmdR9rONz_x1HxfU2-de_provinzial_logo_transparent.png",
    "https://v3b.fal.media/files/b/0a99f0c9/AD9ErSyDODyawyx7c9TWs_provinzial_branding_kit.jpg",
    "https://v3b.fal.media/files/b/0a99f0c9/-Ny7A4qgs2bUHAsBi_L27_provinzial_design_richtlinien.jpg",
]
REFERENCE_ATTACHMENTS = [{"url": u} for u in REF_URLS]

# Each entry: (ad_name, pillar_short, prompt, caption)
DAYS = [
    # Day 1
    ("Family at New Home", "Sicherheit im Alltag",
     "9:16. A young German couple in their early 30s sitting on the wooden floor of their new living room with their toddler between them, surrounded by moving boxes, smiling and relaxed. Warm afternoon light through a large window. Modest, contemporary NRW apartment. Natural lifestyle photography, no posed look, soft warm green color grading aligned with the Provinzial palette (#005940). Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Dein neues Zuhause. Dein neuer Anfang. 🏡\nWir sind da, wenn es darauf ankommt.\nJetzt informieren → Link in Bio\n\n#Provinzial #Versicherung"),
    # Day 2
    ("Hausrat vs Wohngebäude Explainer", "Produktaufklärung",
     "9:16. Clean editorial graphic on a solid Provinzial green (#005940) background. Centered modern sans-serif headline in white: 'Hausrat oder Wohngebäude?'. Below in smaller white text: 'Wir erklären den Unterschied.' Bottom half: a clean line illustration of a small house silhouette in yellow (#FFD000). Generous whitespace, no decorative fonts, clear hierarchy. The yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Hausrat oder Wohngebäude? Zwei Versicherungen, ein Zuhause. 🏠\nWir machen es einfach für dich.\nMehr erfahren → Link in Bio\n\n#Provinzial #Hausrat"),
    # Day 3
    ("NRW Kleinstadt Café", "Regional & Gemeinschaft",
     "9:16. A summer evening in a small NRW Kleinstadt square in Westfalen. A multi-generational family is gathered at an outdoor café table — grandfather, mother, two children. Candid, warm, golden-hour lighting. Authentic German Kleinstadt atmosphere with a soft church spire in the background. Real lifestyle reportage photography, not staged. Warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Heimat ist, wo Generationen zusammenkommen. 🌳\nRegional verwurzelt. Persönlich.\nBerater vor Ort finden → Link in Bio\n\n#Provinzial #NRW"),
    # Day 4
    ("Daughter Moving Out", "Vorsorge & Zukunft",
     "9:16. A father in his late 30s helping his teenage daughter pack a suitcase for her first day of university in her sunlit bedroom. Real, candid emotion, both laughing. Contemporary middle-class NRW family home, soft warm natural light through the window. Authentic lifestyle photography, no stock-photo feel. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Sie zieht aus. Du planst voraus. 🎓\nFür das, was wirklich zählt.\nVorsorge gestalten → Link in Bio\n\n#Provinzial #Vorsorge"),
    # Day 5
    ("Calm Phone Call", "Schaden & Service",
     "9:16. Medium close-up of a middle-aged German woman in her kitchen, holding her phone to her ear with a calm, relieved expression. A kettle on the stove and a coffee cup softly out of focus in the background. Warm natural morning light from a side window. Lifestyle photography, real emotion of being taken care of. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Ein Anruf. Eine echte Stimme. Schnelle Hilfe. ☎️\nWir sind da, wenn es darauf ankommt.\nSchadenservice → Link in Bio\n\n#Provinzial #Service"),
    # Day 6
    ("Kreisliga Saturday", "Regional & Gemeinschaft",
     "9:16. A local NRW Sunday football match (Kreisliga level) in a small village stadium. Families watching from the sidelines, children running, summer sun. Casual community atmosphere, warm authentic colors, no commercial gloss. Real reportage lifestyle photography. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Vereine, Plätze, Menschen. Hier sind wir zu Hause. ⚽\nRegional verwurzelt. Persönlich.\n\n#Provinzial #NRW"),
    # Day 7
    ("Sunday Still Life", "Sicherheit im Alltag",
     "9:16. A warm still-life detail on a wooden kitchen table at golden hour — a set of house keys, a small leather wallet, a slim notebook, and a steaming coffee cup. Warm side lighting from a window, soft shadows. Minimalist composition, real depth, lifestyle aesthetic. The corner of a German home interior softly visible in the background. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Die wichtigen Dinge sind oft die kleinen. 🔑\nSicherheit. Klarheit. Provinzial.\n\n#Provinzial"),
    # Day 8
    ("Child Seat in Wagon", "Sicherheit im Alltag",
     "9:16. A man in his late 30s loading a child car seat into the back of a modern station wagon on a quiet suburban NRW street, morning light, casual weekend outfit. Real, candid lifestyle photography, not staged. Trees softly in the background. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Die wichtigste Fracht. Jeden Tag. 🚗\nFür das, was wirklich zählt.\nKfz-Versicherung berechnen → Link in Bio\n\n#Provinzial #Kfz"),
    # Day 9
    ("Selbstbehalt Explainer", "Produktaufklärung",
     "9:16. Clean editorial graphic on a solid Provinzial green (#005940) background. Centered modern sans-serif headline in white: 'Was ist ein Selbstbehalt?'. Below, a clean line illustration in yellow (#FFD000): a simple shield outline with a small euro symbol inside. Generous whitespace, modern typography, no decorative fonts, clear hierarchy. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Selbstbehalt: Was bedeutet das eigentlich? 💡\nWir erklären es ohne Fachchinesisch.\nMehr erfahren → Link in Bio\n\n#Provinzial #Versicherungswissen"),
    # Day 10
    ("Bäcker um die Ecke", "Regional & Gemeinschaft",
     "9:16. A baker in his 50s handing fresh bread across the counter to an elderly customer in a traditional German neighborhood bakery in NRW. Warm interior light, real working environment, candid moment, authentic local atmosphere with no stock-photo feel. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Vertrauen baut sich Tag für Tag auf. 🥖\nRegional verwurzelt. Persönlich.\nBerater in deiner Nähe finden → Link in Bio\n\n#Provinzial"),
    # Day 11
    ("Renovating Couple", "Vorsorge & Zukunft",
     "9:16. A young couple in their mid-30s standing in the empty kitchen of a half-renovated NRW family house, paint cans on the floor, smiling and looking around at the work ahead. Warm late afternoon light through tall windows. Real candid lifestyle photography, authentic atmosphere. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Vom Traum zum Zuhause. 🏗️\nWir planen mit dir die Sicherheit dazu.\nBauherrenhaftpflicht → Link in Bio\n\n#Provinzial #Eigenheim"),
    # Day 12
    ("Adjuster Handshake", "Schaden & Service",
     "9:16. A claims adjuster in his early 40s — friendly and approachable in a casual polo shirt — shaking hands with a homeowner outside a modest German NRW house with a small water-damaged wall softly in the background. Calm, reassuring moment, real lifestyle photography, warm natural afternoon light. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Ein Gesicht. Ein Handschlag. Eine Lösung. 🤝\nWir sind da, wenn es darauf ankommt.\n\n#Provinzial #Schadenservice"),
    # Day 13
    ("Schützenfest Family", "Regional & Gemeinschaft",
     "9:16. A young NRW family at a Schützenfest (traditional shooting festival) in summer evening light — kids holding ice cream, music tents softly visible in the background. Warm community atmosphere, authentic German Volksfest, real lifestyle reportage photography, no commercial gloss. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Sommer in NRW. Tradition zum Anfassen. 🎪\nRegional verwurzelt. Persönlich.\n\n#Provinzial #NRW"),
    # Day 14
    ("Morgens Klarheit", "Sicherheit im Alltag",
     "9:16. A morning still-life detail of a German kitchen — sunlight cutting across a wooden table, a half-drunk coffee cup, a folded newspaper, a pair of reading glasses, and the corner of a yellow folder lying naturally on the surface. Warm side light, lifestyle still-life photography, real depth. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Morgens wissen, dass alles geklärt ist. ☕\nSicherheit. Klarheit. Provinzial.\n\n#Provinzial"),
    # Day 15
    ("Helmet Strap", "Sicherheit im Alltag",
     "9:16. A mother in her late 30s adjusting a bicycle helmet strap on her 8-year-old son in the driveway of a NRW family home on a sunny morning. Real candid moment, mom focused, son laughing softly. Warm natural light, lifestyle photography, not staged. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Sicherheit beginnt mit den kleinen Gesten. 🚲\nFür das, was wirklich zählt.\nPrivathaftpflicht → Link in Bio\n\n#Provinzial #Familie"),
    # Day 16
    ("Haftpflicht Explainer", "Produktaufklärung",
     "9:16. Editorial graphic on a solid Provinzial green (#005940) background. Centered modern sans-serif headline in white: 'Privathaftpflicht — die wichtigste Versicherung?'. Below, a clean line illustration in yellow (#FFD000) of two stick-figure silhouettes, one accidentally bumping into the other and spilling something. Generous whitespace, modern typography, no decorative fonts, clear hierarchy. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Ein Missgeschick. Schnell teuer. 💶\nWir erklären, warum die Privathaftpflicht so wichtig ist.\nJetzt informieren → Link in Bio\n\n#Provinzial #Haftpflicht"),
    # Day 17
    ("Volunteer Firefighter", "Regional & Gemeinschaft",
     "9:16. A volunteer firefighter (Freiwillige Feuerwehr) in his late 40s, wearing his uniform, standing in front of his small village fire station in NRW. Warm late afternoon light, proud and calm expression, authentic German Dorf atmosphere softly in the background. Documentary lifestyle photography. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Helden des Alltags. Wir stehen an ihrer Seite. 🚒\nRegional verwurzelt. Persönlich.\n\n#Provinzial #Ehrenamt"),
    # Day 18
    ("Großmutter und Enkel", "Vorsorge & Zukunft",
     "9:16. A grandmother in her late 60s playing chess with her 10-year-old grandson in the sunlit garden of a NRW family home. Both focused, smiling, real moment. Lush summer greens softly in the background. Warm afternoon light, authentic lifestyle photography, not staged. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Was wir heute planen, schenken wir morgen weiter. ♟️\nFür das, was wirklich zählt.\nAltersvorsorge → Link in Bio\n\n#Provinzial #Vorsorge"),
    # Day 19
    ("Schaden in 2 Minuten", "Schaden & Service",
     "9:16. Close-up of a hand holding a smartphone showing a clean, calm 'Schaden gemeldet' confirmation screen with a green checkmark. The phone is held over a kitchen counter with a small plant and a glass of water softly out of focus in the background. Warm soft lighting, real lifestyle environment. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Schaden melden in 2 Minuten. Echt. ✅\nWir sind da, wenn es darauf ankommt.\n\n#Provinzial #Service"),
    # Day 20
    ("Sunrise Landstraße", "Regional & Gemeinschaft",
     "9:16. Early morning on a quiet rural NRW road — a cyclist in casual clothes rides past green summer fields, dew on the grass, a small village church spire softly in the distance. Warm sunrise light, calm authentic landscape lifestyle photography. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Morgens auf Landstraßen, die unsere sind. 🚴\nRegional verwurzelt. Persönlich.\n\n#Provinzial #NRW"),
    # Day 21
    ("Altbau Balkon", "Sicherheit im Alltag",
     "9:16. A young woman in her late 20s sitting on the balcony of a NRW Altbau apartment, reading a book, a small potted plant beside her, summer evening light. Calm, candid moment of contentment. Authentic German Altbau atmosphere, real lifestyle photography. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Wenn der Tag leise wird, weißt du, dass alles passt. 🌿\nSicherheit. Klarheit. Provinzial.\n\n#Provinzial"),
    # Day 22
    ("Road Trip Packing", "Sicherheit im Alltag",
     "9:16. A family of four (parents in their late 30s, two kids around 8 and 11) loading luggage into the trunk of a family station wagon in the driveway of a NRW home, ready for a summer road trip. Warm late morning light, real candid moment, smiles and a bit of chaos. Lifestyle photography aesthetic. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Urlaub beginnt, wenn du sicher losfährst. 🧳\nFür das, was wirklich zählt.\nReise- und Kfz-Schutz → Link in Bio\n\n#Provinzial #Sommer"),
    # Day 23
    ("BU Explainer", "Produktaufklärung",
     "9:16. Editorial graphic on a solid Provinzial green (#005940) background. Centered modern sans-serif headline in white: 'Berufsunfähigkeit — einfach erklärt.'. Below, a clean line illustration in yellow (#FFD000) of a desk with a small lamp, abstract and minimal. Generous whitespace, modern typography, no decorative fonts, clear hierarchy. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Wenn der Beruf plötzlich pausieren muss. 💼\nWir erklären die BU-Versicherung ohne Fachchinesisch.\nMehr erfahren → Link in Bio\n\n#Provinzial #BU"),
    # Day 24
    ("Wochenmarkt Tomaten", "Regional & Gemeinschaft",
     "9:16. A small NRW Wochenmarkt scene — a customer in her 50s buying tomatoes from a regional farmer at a wooden market stall, mid-conversation, warm summer morning light. Authentic German Marktplatz atmosphere, real lifestyle reportage photography. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Regional einkaufen. Regional versichern. 🍅\nRegional verwurzelt. Persönlich.\n\n#Provinzial #NRW"),
    # Day 25
    ("Couple Walking Meadow", "Vorsorge & Zukunft",
     "9:16. A couple in their early 50s walking through a meadow on a summer evening near a small NRW village, holding hands, warm golden-hour backlight. Calm, real, candid lifestyle photography, no stock-photo feel. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Der Plan für später beginnt heute. 🌾\nFür das, was wirklich zählt.\nAltersvorsorge gestalten → Link in Bio\n\n#Provinzial #Vorsorge"),
    # Day 26
    ("Service Agent Portrait", "Schaden & Service",
     "9:16. A close-up portrait of a friendly female Provinzial customer service agent (mid-30s, warm smile, in a professional polo shirt) at her desk in a modern, calm office environment in NRW. Soft natural light from a window. Real, approachable lifestyle portrait photography, not staged. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Eine echte Person. Kein Skript. 💚\nWir sind da, wenn es darauf ankommt.\nService-Hotline → Link in Bio\n\n#Provinzial #Service"),
    # Day 27
    ("Stadtpark Konzert", "Regional & Gemeinschaft",
     "9:16. An open-air summer concert in a NRW Stadtpark — a young crowd standing in front of a small local stage at golden hour, hands lifted, joyful authentic atmosphere. Real lifestyle reportage photography, no commercial gloss. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Sommer in NRW. Voller Momente, die zählen. 🎶\nRegional verwurzelt. Persönlich.\n\n#Provinzial"),
    # Day 28
    ("Vater und Sohn Werkstatt", "Sicherheit im Alltag",
     "9:16. A father and his teenage son working on a bicycle together in a sunlit German garage on a Sunday morning, tools laid out on a wooden workbench, real candid moment, warm side light. Authentic lifestyle photography, NRW family home aesthetic. Subtle warm green color grading. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Wir geben weiter, was zählt. 🛠️\nSicherheit. Klarheit. Provinzial.\n\n#Provinzial"),
    # Day 29
    ("Brand Statement Plate", "Sicherheit im Alltag",
     "9:16. Editorial brand statement plate on a solid Provinzial green (#005940) background. Centered, large modern sans-serif text in white: 'Sicherheit. Klarheit. Provinzial.'. Below the headline, a single subtle yellow (#FFD000) horizontal line. Maximum whitespace, minimal, calm composition, no decorative fonts. The yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Drei Worte. Ein Versprechen. 🟡\nSicherheit. Klarheit. Provinzial.\n\n#Provinzial"),
    # Day 30
    ("Welche Versicherung", "Produktaufklärung",
     "9:16. Editorial graphic on a solid Provinzial green (#005940) background. Centered modern sans-serif headline in white: 'Welche Versicherung passt zu mir?'. Below, a clean minimal line illustration in yellow (#FFD000) of a small decision-tree with three branches. Generous whitespace, modern typography, no decorative fonts, clear hierarchy. Yellow Goldene Flügel Provinzial wings logo as a small watermark in the bottom-right corner.",
     "Du fragst dich, was wirklich passt? 🧭\nWir gehen es gemeinsam durch — persönlich vor Ort oder digital.\nBeratung anfragen → Link in Bio\n\n#Provinzial #Beratung"),
]


def main():
    assert len(DAYS) == 30, f"expected 30 days, got {len(DAYS)}"

    base_index = get_next_index()
    print(f"Starting Index = {base_index}")
    print(f"Start date     = {START.isoformat()}")
    print(f"End date       = {(START + timedelta(days=29)).isoformat()}")
    print()

    records = []
    for i, (ad_name, pillar, prompt, caption) in enumerate(DAYS):
        scheduled = (START + timedelta(days=i)).isoformat()
        records.append({
            "Index": base_index + i,
            "Ad Name": f"Provinzial - Day {i+1} - {ad_name} [{pillar}]",
            "Product": "Provinzial",
            "Reference Images": REFERENCE_ATTACHMENTS,
            "Image Prompt": prompt,
            "Image Model": "Nano Banana Pro",
            "Image Status": "Pending",
            "Caption": caption,
            "Scheduled Date": scheduled,
        })

    print(f"Submitting {len(records)} records in batches of 10...")
    created = create_records_batch(records)
    print()
    print(f"Created {len(created)} Airtable records.")


if __name__ == "__main__":
    main()
