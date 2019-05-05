from paths import ALIASES_FILE
from fuzzywuzzy import fuzz

FUZZ_SCORE_THRESHOLD = 0.3
WEIGHT_SIMPLE = 1.
WEIGHT_PARTIAL = 0.6


class StructureAliases:
    def __init__(self):
        self.roi = {}
        self.load()

    @property
    def template_rois(self):
        rois = list(self.roi)
        rois.sort()
        return rois

    def get_aliases(self, template_roi):
        if template_roi in self.roi:
            return self.roi[template_roi]
        return []

    @property
    def all_rois(self):
        rois = []
        for roi in list(self.roi):
            rois.append(roi)
            rois = rois + self.get_aliases(roi)
        return rois

    def has_aliases(self, template_roi):
        return bool(self.get_aliases(template_roi))

    def load(self):
        with open(ALIASES_FILE, 'r') as document:
            for line in document:
                data = line.split(',')
                template_roi = data.pop(0)
                template_roi = template_roi.strip()
                self.roi[template_roi] = [alias.strip() for alias in data if alias.strip()]
                self.roi[template_roi].sort()

    def save(self):
        data = '\n'.join(self.get_csv_lines())
        with open(ALIASES_FILE, 'w') as document:
            document.write(data)

    def get_csv_line(self, template_roi):
        return ','.join([template_roi] + self.get_aliases(template_roi))

    def get_csv_lines(self):
        return [self.get_csv_line(roi) for roi in self.template_rois]

    def add_template_roi(self, template_roi, aliases=None):
        if template_roi not in list(self.roi):
            if aliases is None:
                aliases = []
            self.roi[template_roi] = aliases

    def delete_template_roi(self, template_roi):
        if template_roi in list(self.roi):
            self.roi.pop(template_roi)

    def get_best_roi_match(self, roi):
        fuzz_scores = get_combined_fuzz_scores(roi, self.all_rois)
        return fuzz_scores[0][1], fuzz_scores[0][0]

    def get_best_template_roi_match(self, roi):
        best_match, best_score = self.get_best_roi_match(roi)
        for template_roi in list(self.roi):
            if template_roi == best_match:
                return template_roi, roi, best_score
            for alias in self.roi[template_roi]:
                if alias == best_match:
                    return template_roi, roi, best_score
        return None, roi, 0.

    def match_protocol_rois(self, protocol_rois, plan_rois):
        template_rois, rois, scores = [], [], []
        for plan_roi in plan_rois:
            ans = self.get_best_template_roi_match(plan_roi)
            template_rois.append(ans[0])
            rois.append(ans[1])
            scores.append(ans[2])
            # print(plan_roi, ans)

        scores_by_template_roi = {}
        for i, template_roi in enumerate(template_rois):
            if template_roi not in scores_by_template_roi:
                scores_by_template_roi[template_roi] = {'roi': [], 'score': []}
            scores_by_template_roi[template_roi]['roi'].append(rois[i])
            scores_by_template_roi[template_roi]['score'].append(scores[i])

        protocol_matches = {}
        for protocol_roi in protocol_rois:
            if protocol_roi in list(scores_by_template_roi):
                max_score = max(scores_by_template_roi[protocol_roi]['score'])
                if max_score < FUZZ_SCORE_THRESHOLD:
                    protocol_matches[protocol_roi] = None
                else:
                    max_index = scores_by_template_roi[protocol_roi]['score'].index(max_score)
                    protocol_matches[protocol_roi] = scores_by_template_roi[protocol_roi]['roi'][max_index]

        return protocol_matches


def get_combined_fuzz_score(a, b, simple=None, partial=None):
    a = clean_name(a)
    b = clean_name(b)

    if simple:
        w_simple = float(simple)
    else:
        w_simple = 1.

    if partial:
        w_partial = float(partial)
    else:
        w_partial = 1.

    simple = fuzz.ratio(a, b) * w_simple
    partial = fuzz.partial_ratio(a, b) * w_partial
    combined = float(simple) * float(partial) / 10000.
    return combined


def get_combined_fuzz_scores(string, list_of_strings, simple=WEIGHT_SIMPLE, partial=WEIGHT_PARTIAL):
    scores = [get_combined_fuzz_score(string, string_b, simple=simple, partial=partial) for string_b in list_of_strings]
    order_index = sorted(range(len(scores)), key=lambda k: scores[k])

    return [(scores[i], list_of_strings[i]) for i in order_index[::-1]]


def clean_name(name):
    if isinstance(name, str):
        name = [name]
    return [n.replace('_', '').replace(' ', '').lower() for n in name]
