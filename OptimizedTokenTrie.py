from collections import deque
from copy import deepcopy
from typing import List, Tuple
nil = object()  # used to distinguish from None


class TrieNode(object):

    def __init__(self, token):
        self.token = token
        self.children = {}
        self.depth = None
        # indication of possible termination of token sequence
        self.word_finished = False
        # How many times this character appeared in the addition process
        self.counter = 1
        self.output = nil  # an output function for this node
        self.fail = nil  # this is used by aho corasick when the trie gets compressed into the directed acyclic wor graph

    def __repr__(self):
        # this method will stringify the node

        if self.output is not nil:
            return "<TrieNode '%s' '%s'>" % (self.token, self.output)
        else:
            return "<TrieNode '%s'>" % self.token


class OptimizedTokenTrie(object):


    def __init__(self, tokenizer_model):
        self.unique_token_set = set()
        self.root = TrieNode('')
        self.root.depth = 0
        self.tokenizer_model = tokenizer_model
        self.max_depth = 0
        self.inserted_tokens = set()
        self.reference_text_tokens = set()
        self.s_doc_tokens = None

    def __get_node(self, token_sequence):

        node = self.root
        for tok in token_sequence:
            try:
                node = node.children[tok]
            except KeyError:
                return None

        return node

    def get(self, token_sequence, default=nil):
        # retrieves item if token sequence exists in the trie and raises key error otherwise as in a normal python data structure
        doc = self.tokenizer_model(token_sequence)
        token_sequence = [tok.text for tok in doc]
        node = self.__get_node(token_sequence)
        output = nil
        if node:
            output = node.output

        if output is nil:
            if default is nil:
                raise KeyError("no key '%s'" % token_sequence)
            else:
                return default
        else:
            return output

    def keys(self):
        # this will return all items currently stored in the data structure

        for key, _ in self.items():
            yield key

    def values(self):
        # returns all associated values in the data structure

        for _, value in self.items():
            yield value

    def items(self):
        # similar to python dictionary bindings this method returns associative pairs for the data contained

        L = []

        def aux(node, s):
            s = s + " " + node.token
            if node.output is not nil:
                L.append((tuple(s.split()), node.output))

            for child in node.children.values():
                if child is not node:
                    aux(child, s)

        aux(self.root, '')
        return iter(L)

    def number_of_tokens(self):
        # calculates number of stored tokens total including duplicates

        stack = deque()
        stack.append(self.root)
        n = 0
        while stack:
            node = stack.pop()
            n += node.counter

            for child in node.children.values():
                stack.append(child)

        return n

    def generate_unique_token_set(self):
        # calculates number of stored tokens total including duplicates

        stack = deque()
        stack.append(self.root)
        while stack:
            node = stack.pop()
            if node != self.root:
                self.unique_token_set.add(node.token)

            for child in node.children.values():
                stack.append(child)

        return self.unique_token_set

    def __len__(self):
        # native binding that calculates number of stored token sequences including duplicates

        stack = deque()
        stack.append(self.root)
        n = 0
        while stack:
            node = stack.pop()
            if node.output is not nil:
                n += node.counter

            for child in node.children.values():
                stack.append(child)

        return n

    def add_token_sequence(self, token_sequence: Tuple[str], value):

        # adds token sequence into data structure and update counters at each node
        # also updates the maximum token sequence length so our search space is minimized for the reference text
        self.max_depth = max(self.max_depth, len(token_sequence))
        if not token_sequence:
            return

        node = self.root
        for i, tok in enumerate(token_sequence):
            self.inserted_tokens.add(tok)
            try:
                node = node.children[tok]
                node.counter += 1
            except KeyError:
                n = TrieNode(tok)
                n.depth = node.depth + 1
                node.children[tok] = n
                node = n
        node.word_finished = True

        node.output = value

    def clear(self):
        # clears out the data

        self.root = TrieNode('')

    def exists(self, word):
        # check if token sequence is in DS

        node = self.__get_node(word)
        if node:
            return bool(node.output != nil)
        else:
            return False

    def generate_reference_text_tokens(self, reference_text):

        s_doc_tokens = self.tokenizer_model(reference_text.strip())
        self.s_doc_tokens = s_doc_tokens
        for token in s_doc_tokens:
            self.reference_text_tokens.add(token.text)
        # self.reference_text_tokens.remove('')

    def match(self, word):
        # check for matched prefix
        doc = self.tokenizer_model(word)
        token_sequence = [tok.text for tok in doc]
        return (self.__get_node(token_sequence) is not None)

    def make_automaton(self):
        """
		Converts trie to Aho-Corasick automaton.
		"""
        # self.reference_text_tokens.remove('')
        queue = deque()

        # 1.
        # print(self.root.children)
        for token in (self.reference_text_tokens | self.inserted_tokens):
            # print(token)
            if token in self.root.children:
                node = self.root.children[token]
                if node.token != '':
                    node.fail = self.root  # f(s) = 0
                    # print(node, node.children)
                    queue.append(node)
            else:
                self.root.children[token] = self.root

        # 2.
        # print(queue)
        while queue:
            r = queue.popleft()
            # print('children:', r.children.keys())
            # print(r.children.values())
            for node in r.children.values():
                queue.append(node)
                state = r.fail
                # print(node.token, state.children.keys())

                while node.token not in state.children:
                    # print('not in:', state, node.token)
                    state = state.fail
                # print(self.root, self.root.fail)
                node.fail = state.children.get(node.token, self.root)

    def find_all_search_spans(self, string):
        """
		Generator performs Aho-Corasick search string algorithm, yielding
		tuples containing two values:
		- position in string
		- outputs associated with matched strings
		"""
        self.generate_reference_text_tokens(string)
        self.make_automaton()
        state = self.root
        # print(state)
        for index, token in enumerate(self.s_doc_tokens):

            while token.text not in state.children:
                # print(state, state.children)
                state = state.fail

            state = state.children.get(token.text, self.root)

            tmp = state

            output = []
            while tmp is not nil:
                if tmp.output is not nil:
                    # print('depth:', tmp.depth)
                    output.append((tmp.output, tmp.depth))
                    # print(output)
                tmp = tmp.fail

            if output:
                # print(self.s_doc_tokens[index])
                # print('index', index, output)
                for out in output:
                    # print('dasda')
                    output_token_span = self.s_doc_tokens[index - (out[1] - 1):index + 1]
                    start_char = output_token_span.start_char
                    end_char = output_token_span.end_char
                    yield string[start_char: end_char], start_char, end_char

    # def find_all_search_spans(self, string):
    #     # returns the corresponding char intervals for the strings in the reference text for the token Trie nodes
    #
    #     s_doc_tokens = self.tokenizer_model(string.strip())
    #     for window_size in range(1, self.max_depth+1):
    #         for start_index in range(len(s_doc_tokens)-window_size):
    #             doc_span = s_doc_tokens[start_index:start_index+window_size]
    #             try:
    #                 self.get(doc_span.text)
    #                 # print(doc_span)
    #                 yield doc_span.text, doc_span.start_char, doc_span.end_char
    #             except KeyError:
    #                 continue

