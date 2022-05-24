# Copyright (c) 2021, NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nemo_text_processing.text_normalization.de.utils import get_abs_path, load_labels
from nemo_text_processing.text_normalization.en.graph_utils import (
    NEMO_NOT_QUOTE,
    NEMO_SIGMA,
    GraphFst,
    delete_preserve_order,
)

try:
    import pynini
    from pynini.lib import pynutil

    PYNINI_AVAILABLE = True
except (ModuleNotFoundError, ImportError):
    PYNINI_AVAILABLE = False


class DateFst(GraphFst):
    """
    Finite state transducer for verbalizing date, e.g.
        date { day: "vier" month: "april" year: "zwei tausend zwei" } -> "vierter april zwei tausend zwei"
        date { day: "vier" month: "mai" year: "zwei tausend zwei" } -> "vierter mai zwei tausend zwei"

    Args:
        ordinal: ordinal verbalizer GraphFst
        deterministic: if True will provide a single transduction option,
            for False multiple transduction are generated (used for audio-based normalization)

        tokens { date { day: "vier und zwanzig" month: "Mai" year: "zwei tausend zwei und zwanzig" preserve_order: true } }
        =>
        day: "vier und zwanzig" month: "Mai" year: "zwei tausend zwei und zwanzig" preserve_order: true
        day: "ordinal_stem"+ ten

        tokens {  ordinal { integer: "vier und zwanzig"  }  } #If called through ordinal, not date
    """

    def __init__(self, ordinal: GraphFst, deterministic: bool = True):
        super().__init__(name="date", kind="verbalize", deterministic=deterministic)

        suffixes = pynini.union("ten", "te")
        convert_rest = pynutil.insert(suffixes, weight=0.1)

        day_cardinal = pynutil.delete("day: \"") + pynini.closure(NEMO_NOT_QUOTE, 1) + pynutil.delete("\"")
        # day = day_cardinal @ pynini.cdrewrite(ordinal.ordinal_stem, "", "[EOS]", NEMO_SIGMA) + pynutil.insert("ten") # original
        # My version:
        day = day_cardinal @ pynini.cdrewrite(pynini.closure(ordinal.ordinal_stem, 0, 1) + convert_rest, "", "[EOS]", NEMO_SIGMA).optimize()

        months_names = pynini.union(*[x[1] for x in load_labels(get_abs_path("data/months/abbr_to_name.tsv"))])
        month = pynutil.delete("month: \"") + pynini.closure(NEMO_NOT_QUOTE, 1) + pynutil.delete("\"")
        final_month = month @ months_names
        final_month |= month @ pynini.difference(NEMO_SIGMA, months_names) @ pynini.cdrewrite(
            ordinal.ordinal_stem, "", "[EOS]", NEMO_SIGMA
        ) + pynutil.insert("ter")

        year = pynutil.delete("year: \"") + pynini.closure(NEMO_NOT_QUOTE, 1) + pynutil.delete("\"")

        # day month year
        graph_dmy = day + pynini.accep(" ") + final_month + pynini.closure(pynini.accep(" ") + year, 0, 1)
        graph_dmy |= final_month + pynini.accep(" ") + year

        self.graph = graph_dmy | year
        final_graph = self.graph + delete_preserve_order

        delete_tokens = self.delete_tokens(final_graph)
        self.fst = delete_tokens.optimize()


## DEBUG##

from pynini.lib import pynutil

def apply_fst(text, fst):
  """ Given a string input, returns the output string
  produced by traversing the path with lowest weight.
  If no valid path accepts input string, returns an
  error.
  """
  try:
     print(pynini.shortestpath(text @ fst).string())
  except pynini.FstOpError:
    print(f"Error: No valid output with given input: '{text}'")

if __name__ == "__main__":
    cardinal = DateFst().fst
    example = 'tokens { date { day: "1" month: "Januar" }'

    apply_fst(example, cardinal)