from nemo_text_processing.text_normalization.normalize import Normalizer

class Normalise:
    """
    Main class
    """
    def __init__(self, lang, input_case="caps", whitelist=None, verbose=False) -> None:
        assert lang in ["de", "en", "es", "ru"]
        if not whitelist:
            whitelist = f"nemo_text_processing/text_normalization/{lang}/data/whitelist_custom.tsv"
        self.normalizer = Normalizer(input_case=input_case, lang=lang, whitelist=whitelist)
        self.verbose = verbose
    
    def post_process(self, text) -> str:
        # TODO: implement
        return text

    def __call__(self, text) -> str:
        normalised = self.normalizer.normalize(text, verbose=self.verbose)
        processed = self.post_process(normalised)
        return processed

"""
# from run_predict.py
args = parse_args()
file_path = args.input
normalizer = Normalizer(input_case=args.input_case, lang=args.language, whitelist=args.whitelist)
print("Loading data: " + file_path)

# TODO: No need to load any file, just taking input directly
# Might need to modify NeMo code to just take single sentence
# -> Alternative: one sentence list or whatever structure (probably easier to implement)
data = load_file(file_path)
print("- Data: " + str(len(data)) + " sentences")

normalizer_prediction = normalizer.normalize_list(data, verbose=args.verbose)

# Don't need that write function
write_file(args.output, normalizer_prediction)
print(f"- Normalized. Writing out to {args.output}")
"""
if __name__ == "__main__":
    norm = Normalise("de", input_case="cased")
    normalised = norm("Dr. Hunt kam um ca. 23:48 Uhr ins Büro der EU.")
    print(normalised)
    # input_case = lower_cased:
    # Dr. Hunt kam um c a . drei und zwanzig uhr acht und vierzig ins Büro der EU.
    # only works with lowercase input, maybe not a good idea for german.

    # input_case = cased:
    # doctor Hunt kam um ca. drei und zwanzig uhr acht und vierzig ins Büro der e u .

    # input_case = caps:
    # DOCTOR Hunt kam um ca. drei und zwanzig uhr acht und vierzig ins Büro der E U .

    # TODO:
    # adjust whitelist for ca. and DOCTOR
    # -> currently uses .upper() for case = caps. Better to upper-case the whitelist and take that out of the code. More flexible
    # Ideally shouldn't need the case "caps"