import math
import string
import spacy
import sys
import re
from db_access.ngram_dist_db import ObjectDistributionsSQLite, DistEnum

sys.dont_write_bytecode = True

PSEUDO_COUNT = 5


class TrueCaser:
    def __init__(self):
        self.obj_dist_sqlite = ObjectDistributionsSQLite.check_and_connect()
        self.nlp = spacy.load('en')

    def _get_denom(self, gram_dict):
        return sum(gram_dict.values()) + 3 * PSEUDO_COUNT

    def _get_highest_scoring_token(self, distributions, token):
        best_score = float("-inf")
        best_token = None
        for adjusted_token in [token.title(), token.upper(), token.lower()]:
            score = 0
            for gram in DistEnum:
                denom = self._get_denom(distributions[gram])
                score += math.log((distributions[gram].get(adjusted_token,
                                                           0) + PSEUDO_COUNT) / denom)
            if score > best_score:
                best_score = score
                best_token = adjusted_token
        return best_token

    def _get_best_token(self, prev_token, token, next_token):
        full_tokens_to_query = {DistEnum.uni: self._get_full_tokens(None, token, None)}

        if prev_token is not None:
            full_tokens_to_query[DistEnum.back_bi] = self._get_full_tokens(prev_token, token, None)

        if next_token is not None:
            full_tokens_to_query[DistEnum.fwd_bi] = self._get_full_tokens(None, token, next_token)

            if prev_token is not None:
                full_tokens_to_query[DistEnum.tri] = self._get_full_tokens(
                    prev_token, token, next_token)
        distributions = self.obj_dist_sqlite.select(full_tokens_to_query)
        return self._get_highest_scoring_token(distributions, token)

    def _get_full_tokens(self, prev_token, token, next_token):
        tokens = []
        for t in [token.title(), token.upper(), token.lower()]:
            tokens.append(self._get_combined_token(prev_token, t, next_token))
        return tokens

    def _get_combined_token(self, prev_token, token, next_token):
        new_token = token
        if prev_token is not None:
            new_token = f'{prev_token}_{new_token}'
        if next_token is not None:
            new_token += f'_{next_token}'
        return new_token

    def _get_true_case(self, tokens):
        tokens_true_case = []
        for token_pos, token in enumerate(filter(lambda x: x[0] != "'", tokens)):
            token = token.lower() #just use truecased
            if token in string.punctuation or token.isdigit() or token[0].isupper():
                tokens_true_case.append(token)
            else:
                prev_token = tokens_true_case[token_pos - 1] if token_pos > 0 else None
                next_token = tokens[token_pos + 1].lower() if token_pos < len(tokens) - 1 else None
                best_token = self._get_best_token(prev_token, token.lower(), next_token)
                if token_pos == 0:
                    best_token = best_token.title()
                tokens_true_case.append(best_token)
        return tokens_true_case

    def generate_sentence(self, sentences):
        """responsible for running the truecase model and returning the appropriate truecased sentence"""
        normalcase_tokens = [x.text for x in self.nlp.tokenizer(sentences)]
        truecase_sentence = self._get_true_case(normalcase_tokens)
        truecase_sentence = ' '.join(truecase_sentence)
        return truecase_sentence

    def get_result(self, message):
        whitespace_corrected = self._clean_up_whitespace(message)
        truecased_message = self.generate_sentence(whitespace_corrected)
        return truecased_message

    @classmethod
    def _clean_up_whitespace(cls, message):
        new_message = re.sub('\s+', ' ', message)
        return new_message.strip()
