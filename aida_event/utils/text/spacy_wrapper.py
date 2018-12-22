import spacy


class SpacyWrapper:
    def __init__(self, language_id='en'):
        self.nlp = spacy.load(language_id)

    def __prevent_sentence_boundary_detection(self, doc):
        for token in doc:
            token.is_sent_start = False
        return doc

    def tokenize_on_pretokenized_list(self, token_list):
        tokenization_result = self.nlp.tokenizer.tokens_from_list(token_list)
        tokenization_result = self.__prevent_sentence_boundary_detection(tokenization_result)
        return tokenization_result

    def pos_tagger(self, tokenization_result):
        return self.nlp.tagger(tokenization_result)

    def dep_parser(self, tokenization_result):
        return self.nlp.parser(tokenization_result)