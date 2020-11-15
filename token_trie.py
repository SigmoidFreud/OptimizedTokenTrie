from collections import defaultdict
from typing import Tuple
from typing import List
import spacy
import multiprocessing
# initialize tokenization model
from OptimizedTokenTrie import OptimizedTokenTrie

nlp = spacy.load("en_core_web_sm")

text_list_example = [
             "Borrower",
             "Subsidiaries",
             "Material Project Party",
             "Project",
             "Project Manager",
             "Anti-Money Laundering Laws",
             "Sanctions",
             "Anti-Corruption Laws",
             "Affiliates",
             "Sanctioned Person",
             "Sanctioned Country",
             "Person",
             "Officer",
             "Director",
             "Agents",
            ]

class TextProcessor(object):
    def __init__(self, text_list: List[str]):
        self.n_cpus = cpus = multiprocessing.cpu_count()
        self.batch_size = min(int(len(text_list) / cpus)+1, 10)
        self.processed_tokens_dict = {}
        for doc in nlp.pipe(text_list, disable=["tagger", "parser"], batch_size=self.batch_size, n_process=self.n_cpus):
            # Do something with the doc here
            self.processed_tokens_dict[tuple([str(tok) for tok in doc])] = doc.text

def demo():
    text_processor = TextProcessor(text_list_example)

    ott = OptimizedTokenTrie(nlp)
    token_sequence_dict = text_processor.processed_tokens_dict
    for tok_seq, doc_str in token_sequence_dict.items():
        ott.add_token_sequence(tok_seq, doc_str)

    s = "The operations of each Borrower, and the activities of the officers and directors and, to the knowledge of each Borrower, any Subsidiaries of the Borrowers, employees, agents and representatives of each Borrower, while acting on behalf of such Borrower, and to the knowledge of each Borrower the operations of each Material Project Party in relation to the Project, have been conducted at all times in compliance with all applicable Anti-Money Laundering Laws, Sanctions, and Anti-Corruption Laws. Neither Borrower, nor any Subsidiaries of the Borrowers, nor any officer or director or, to the knowledge of any Borrower, Affiliates, employee, agent or representative of either Borrower has engaged, directly or indirectly, in any activity or conduct which would violate any Anti-Corruption Laws or Anti-Money Laundering Laws. Neither Borrower nor any Subsidiaries of the Borrowers, nor any officer or director or, to the knowledge of any Borrower, Affiliates, employee, agent or representative of either Borrower has engaged, directly or indirectly, in any dealings or transactions with, involving or for the benefit of a Sanctioned Person,or in or involving a Sanctioned Country, where such dealings or transactions would violate Sanctions, in the five (5) year period immediately preceding the date hereof."

    s_doc_tokens = nlp(s)
    print(ott.generate_unique_token_set())
    ott.make_automaton()
    for res in ott.items():
        print(res)
    result_set = defaultdict(list)
    for res in ott.find_all_search_spans(s):
        # print('%s' % s)
        st, start_index, end_index = res
        result_set[st].append((start_index, end_index))
    '''
        The result is a dictionary of the token sequences that appear in the reference text and the value for each key 
        is a list of tuples represent the start and end index of each potential token sequence
    '''
    print(result_set)
    # for res in ott.items():
    #     print(res)
    # # print(ott.number_of_tokens(), len(ott))
    #
    # search_index_map = defaultdict(list)
    # for res in ott.find_all_search_spans(s):
    #     search_index_map[res[0]].append((res[1], res[2]))

    # print('search results:', dict(search_index_map))




if __name__ == "__main__":
    demo()