from nemo_text_processing.text_normalization.normalize import Normalizer
from time import time
import re
class Normalize:
    """
    Main class, mostly based on NeMo's Normalizer with some adjustments.
    Additional post processing
    Class needs to be instantiated once and can then be called directly with text as input
    Example in __main__
    """
    def __init__(self, lang, input_case="cased", whitelist=None, verbose=False) -> None:
        assert lang in ["de", "en", "es", "ru"]
        if not whitelist and not lang=="en":
            # English doesn't need a whitelist passed, it uses a more complex system
            whitelist = f"nemo_text_processing/text_normalization/{lang}/data/whitelist_custom.tsv"
        self.normalizer = Normalizer(input_case=input_case, lang=lang, whitelist=whitelist) # TODO: handle english whitelist, don't just set to none by default, only for en
        self.verbose = verbose
    
    def pre_process(self, text) -> str:
        text = text.translate(str.maketrans('', '', "„\'“\"")) # TODO: test if faster than regex
        text = re.sub("[-–]", " ", text)
        text = re.sub(" {2,}", " ", text) # remove multiple whitespaces (necessary after prev step)
        text = re.sub("(?!\d)\.(?=\d{3}\b)", "", text) # remove dots inbetween numbers
        return text
    
    def post_process(self, text) -> str:
        # remove spaces before punctuation
        text = re.sub(" ([.,?!])", r"\1", text)
        text = text[0].upper() + text[1:]
        return text

    def __call__(self, text, ignore_tags = True) -> str:
        """
        Main normalisation method. Takes unnormalised text as input and returns normalised text as output.
        ignore_tags param is used to ignore SSML tags, such as <break="400ms"> as well as
        """
        if not text:
            raise ("Please input a non-empty string.")
        if ignore_tags:
            sentence = []
            ssml = re.compile("(<[^>]*>>?|{[^}]*}}?)") # Two part regex: <[^>]*>>? matches ssml tags | OR {[^}]*}}? matches Personalisation Parameters
            split_by_tags = ssml.split(text)
            split_by_tags = list(filter(None, split_by_tags))
            for chunk in split_by_tags:
                if chunk.startswith("<") or chunk.startswith("{"):
                    sentence.append(chunk)
                else:
                    preprocessed = self.pre_process(chunk)
                    normalized = self.normalizer.normalize(preprocessed, verbose=self.verbose)
                    sentence.append(normalized)
            normalized_sentence = " ".join(sentence)

        else:
            preprocessed = self.pre_process(text)
            normalized_sentence = self.normalizer.normalize(preprocessed, verbose=self.verbose)

        postprocessed = self.post_process(normalized_sentence)
        return postprocessed
    
if __name__ == "__main__":
    norm = Normalize("de", input_case="cased")
    # normalized = norm('Dr. Hunt kam am 27. \'"März" um ca. 23:48 Uhr ins „Büro“ von CO₂ AFLR.')
    # print(normalized)
    # print(norm.normalizer.normalize("Dr. Hunt kam am 27. März um ca. 23:48 Uhr ins Büro von CO₂ AFLR"))
    # print(norm("der mittlerweile knapp 230000 Mal unterschrieben wurde"))
    # print(norm("der mittlerweile knapp 230.000 Mal unterschrieben wurde"))
    with open ("nemo_text_processing/text_normalization/data/input/test_de.txt", "r") as f:
        lines = [line for line in f.read().split('\n')]
    for line in lines:
        b = time()
        print(f"{line} \n{norm(line)}")
        print(f"{time() - b}\n\n")
    """
    Forbidden input chars:
    "'[]^`{>}~|</\
        -> Probably already handled on the API side. Check with Sam

    # with open("/Users/mabs/Documents/programming/validate_script_and_data/test/data/script/old/heise_filtered2.txt.backup", "r") as f:
    #     lines = f.readlines()
    
    # normalised = [norm(line) for line in lines]

    # #with open("/Users/mabs/Documents/programming/validate_script_and_data/test/data/script/heise_filtered2.txt.backup_normalised", "w") as f:
    # for line in normalised:
    #     print(line)
    # #         f.write(f"{line}\n")
    """