import json
import torch
import numpy as np
import os
from pytorch_pretrained_bert import BertTokenizer


class BertQA:
    def __init__(self, config, mode):
        self.max_len1 = config.getint("data", "max_len1")
        self.max_len2 = config.getint("data", "max_len2")

        self.tokenizer = BertTokenizer.from_pretrained(os.path.join(config.get("model", "bert_path"), "vocab.txt"))
        self.k = config.getint("data", "topk")

    def convert(self, tokens, which, l):
        mask = []
        tokenx = []

        tokens = self.tokenizer.tokenize(tokens)
        ids = self.tokenizer.convert_tokens_to_ids(tokens)

        for a in range(0, len(ids)):
            mask.append(1)
            tokenx.append(which)

        while len(ids) < l:
            ids.append(self.tokenizer.vocab["[PAD]"])
            mask.append(0)
            tokenx.append(which)

        ids = torch.LongTensor(ids)
        mask = torch.LongTensor(mask)
        tokenx = torch.LongTensor(tokenx)

        return ids, mask, tokenx

    def process(self, data, config, mode, *args, **params):
        txt = []
        mask = []
        token = []
        label = []
        idx = []

        for temp_data in data:
            idx.append(temp_data["id"])
            if config.getboolean("data", "multi_choice"):
                label_x = 0
                if "A" in temp_data["answer"]:
                    label_x += 1
                if "B" in temp_data["answer"]:
                    label_x += 2
                if "C" in temp_data["answer"]:
                    label_x += 4
                if "D" in temp_data["answer"]:
                    label_x += 8
            else:
                label_x = 0
                if "A" in temp_data["answer"]:
                    label_x = 0
                if "B" in temp_data["answer"]:
                    label_x = 1
                if "C" in temp_data["answer"]:
                    label_x = 2
                if "D" in temp_data["answer"]:
                    label_x = 3

            label.append(label_x)

            temp_text = []
            temp_mask = []
            temp_token = []

            for option in ["A", "B", "C", "D"]:
                res = temp_data["statement"] + temp_data["option_list"][option]
                text = []

                for a in range(0, len(res)):
                    text = text + [res[a]]
                text = text[0:self.max_len1]

                txt1, mask1, token1 = self.convert(text, 0, self.max_len1)

                ref = []
                k = [0, 1, 2, 6, 12, 7, 13, 3, 8, 9, 14, 15, 4, 10, 16, 5, 16, 17]
                for a in range(0, self.k):
                    res = temp_data["reference"][option][k[a]]
                    text = []

                    for a in range(0, len(res)):
                        text = text + [res[a]]
                    text = text[0:self.max_len2]

                    txt2, mask2, token2 = self.convert(text, 1, self.max_len2)

                    temp_text.append(torch.cat([txt1, txt2]))
                    temp_mask.append(torch.cat([mask1, mask2]))
                    temp_token.append(torch.cat([token1, token2]))

            txt.append(torch.stack(temp_text))
            mask.append(torch.stack(temp_mask))
            token.append(torch.stack(temp_token))

        txt = torch.stack(txt)
        mask = torch.stack(mask)
        token = torch.stack(token)
        label = torch.LongTensor(np.array(label, dtype=np.int32))

        return {"text": txt, "mask": mask, "token": token, 'label': label, "id": idx}
