"""Pre-approved advisory templates (PRD §18: life-safety wording uses approved templates).

English is the reference text. Odia and Bengali templates are SAMPLE translations written for the
demo; they MUST be reviewed by a native-speaking officer before any real use. Place names and shelter
names are kept in English script so they stay unambiguous for review.
"""
STAGES = ["watch", "warning", "evacuation_order", "final_warning"]
LANGUAGES = {"en": "English", "or": "Odia", "bn": "Bengali"}
CAP_LANG = {"en": "en-IN", "or": "or-IN", "bn": "bn-IN"}
REVIEW_NOTE = {
    "en": "Approved English template.",
    "or": "Sample Odia template translation – requires review by a native-speaking officer before dispatch.",
    "bn": "Sample Bengali template translation – requires review by a native-speaking officer before dispatch.",
}

T = {
    "en": {
        "stage": {"watch": "CYCLONE WATCH", "warning": "CYCLONE WARNING", "evacuation_order": "EVACUATION ORDER",
                  "final_warning": "FINAL WARNING"},
        "wind": "strong winds up to {v} km/h",
        "surge": "storm surge flooding up to {d} m",
        "rain": "heavy rain and flooding",
        "sentence": "{stage}: Cyclone {name} – {what} expected in {where} from {when}.",
        "action": {
            "watch": "Keep documents, drinking water, food and medicines ready. Listen to official updates.",
            "warning": "Prepare to leave. Help elderly people, children and persons with disabilities to get ready.",
            "evacuation_order": "Leave now for the cyclone shelter. Do not wait.",
            "final_warning": "Go to the shelter immediately or stay inside a strong building away from the coast.",
        },
        "fishers": "Fishermen must not go to sea; bring boats ashore.",
        "shelter": "Shelter: {shelter}.",
        "no_shelter": "Shelter: nearest strong building on high ground (no shelter reachable by road – call 1070).",
        "authority": "Issued by {authority}.",
    },
    "or": {
        "stage": {"watch": "ବାତ୍ୟା ସତର୍କ ସୂଚନା", "warning": "ବାତ୍ୟା ଚେତାବନୀ", "evacuation_order": "ସ୍ଥାନାନ୍ତରଣ ଆଦେଶ",
                  "final_warning": "ଅନ୍ତିମ ଚେତାବନୀ"},
        "wind": "ଘଣ୍ଟାକୁ {v} କି.ମି. ପର୍ଯ୍ୟନ୍ତ ପ୍ରବଳ ପବନ",
        "surge": "{d} ମିଟର ପର୍ଯ୍ୟନ୍ତ ସମୁଦ୍ର ଜଳ ଉଚ୍ଛ୍ୱାସ",
        "rain": "ପ୍ରବଳ ବର୍ଷା ଓ ବନ୍ୟା",
        "sentence": "{stage}: ବାତ୍ୟା {name} – {where}ରେ {when} ଠାରୁ {what}ର ସମ୍ଭାବନା ଅଛି।",
        "action": {
            "watch": "ଦରକାରୀ କାଗଜପତ୍ର, ପାନୀୟ ଜଳ, ଖାଦ୍ୟ ଓ ଔଷଧ ପ୍ରସ୍ତୁତ ରଖନ୍ତୁ। ସରକାରୀ ସୂଚନା ଶୁଣନ୍ତୁ।",
            "warning": "ଘର ଛାଡିବାକୁ ପ୍ରସ୍ତୁତ ରୁହନ୍ତୁ। ବୟସ୍କ, ଶିଶୁ ଓ ଭିନ୍ନକ୍ଷମ ବ୍ୟକ୍ତିଙ୍କୁ ସାହାଯ୍ୟ କରନ୍ତୁ।",
            "evacuation_order": "ଏବେ ହିଁ ବାତ୍ୟା ଆଶ୍ରୟସ୍ଥଳୀକୁ ଯାଆନ୍ତୁ। ଅପେକ୍ଷା କରନ୍ତୁ ନାହିଁ।",
            "final_warning": "ତୁରନ୍ତ ଆଶ୍ରୟସ୍ଥଳୀକୁ ଯାଆନ୍ତୁ କିମ୍ବା ଉପକୂଳଠାରୁ ଦୂରରେ ଏକ ମଜବୁତ ଘର ଭିତରେ ରୁହନ୍ତୁ।",
        },
        "fishers": "ମତ୍ସ୍ୟଜୀବୀମାନେ ସମୁଦ୍ରକୁ ଯାଆନ୍ତୁ ନାହିଁ; ଡଙ୍ଗା କୂଳକୁ ଆଣନ୍ତୁ।",
        "shelter": "ଆଶ୍ରୟସ୍ଥଳୀ: {shelter}।",
        "no_shelter": "ଆଶ୍ରୟସ୍ଥଳୀ: ଉଚ୍ଚ ସ୍ଥାନରେ ଥିବା ନିକଟତମ ମଜବୁତ ଘର (ରାସ୍ତା ବନ୍ଦ – 1070 କୁ ଫୋନ କରନ୍ତୁ)।",
        "authority": "ଜାରିକର୍ତ୍ତା: {authority}।",
    },
    "bn": {
        "stage": {"watch": "ঘূর্ণিঝড় সতর্কবার্তা", "warning": "ঘূর্ণিঝড় সতর্কতা", "evacuation_order": "সরে যাওয়ার আদেশ",
                  "final_warning": "চূড়ান্ত সতর্কতা"},
        "wind": "ঘণ্টায় {v} কিমি পর্যন্ত প্রবল বাতাস",
        "surge": "{d} মিটার পর্যন্ত জলোচ্ছ্বাস",
        "rain": "ভারী বৃষ্টি ও বন্যা",
        "sentence": "{stage}: ঘূর্ণিঝড় {name} – {where} এলাকায় {when} থেকে {what} হওয়ার সম্ভাবনা রয়েছে।",
        "action": {
            "watch": "প্রয়োজনীয় কাগজপত্র, পানীয় জল, খাবার ও ওষুধ প্রস্তুত রাখুন। সরকারি ঘোষণা শুনুন।",
            "warning": "বাড়ি ছাড়ার জন্য প্রস্তুত থাকুন। বয়স্ক, শিশু ও প্রতিবন্ধী মানুষদের সাহায্য করুন।",
            "evacuation_order": "এখনই ঘূর্ণিঝড় আশ্রয়কেন্দ্রে যান। অপেক্ষা করবেন না।",
            "final_warning": "অবিলম্বে আশ্রয়কেন্দ্রে যান অথবা উপকূল থেকে দূরে কোনো মজবুত বাড়ির ভিতরে থাকুন।",
        },
        "fishers": "মৎস্যজীবীরা সমুদ্রে যাবেন না; নৌকা তীরে তুলে আনুন।",
        "shelter": "আশ্রয়কেন্দ্র: {shelter}।",
        "no_shelter": "আশ্রয়কেন্দ্র: উঁচু জায়গায় নিকটতম মজবুত বাড়ি (রাস্তা বন্ধ – 1070 নম্বরে ফোন করুন)।",
        "authority": "জারি করেছেন: {authority}।",
    },
}


def hazards_phrase(lang: str, wind_kmh: float, surge_m: float, flood_p: float) -> str:
    t = T[lang]
    parts = [t["wind"].format(v=int(round(wind_kmh, -1)))]
    if surge_m >= 0.1:
        parts.append(t["surge"].format(d=f"{surge_m:.1f}"))
    if flood_p >= 0.35:
        parts.append(t["rain"])
    sep = ", " if lang == "en" else ", "
    return sep.join(parts)


def render(lang: str, stage: str, audience: str, *, name: str, where: str, when: str, wind_kmh: float,
           surge_m: float, flood_p: float, shelter: str | None, authority: str) -> dict:
    t = T[lang]
    what = hazards_phrase(lang, wind_kmh, surge_m, flood_p)
    action = t["action"][stage] + (" " + t["fishers"] if audience == "fishers" else "")
    shelter_txt = t["shelter"].format(shelter=shelter) if shelter else t["no_shelter"]
    fields = {"what": what, "where": where, "when": when, "action": action,
              "shelter": shelter or t["no_shelter"], "authority": authority}
    text = " ".join([t["sentence"].format(stage=t["stage"][stage], name=name, what=what, where=where, when=when),
                     action, shelter_txt, t["authority"].format(authority=authority)])
    return {"headline": f"{t['stage'][stage]} – {name} – {where}", "fields": fields, "text": text}
