# -*- coding:utf-8-*-

"""
file: CRF.py

author: Yoann Dupont

MIT License

Copyright (c) 2018 Yoann Dupont

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re
import itertools

UNICODE_LOWERS = (
    "a-zµßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿāăąćĉċčďđēĕėęěĝğġģĥħĩīĭįıĳĵķĸĺļľŀłńņňŉŋōŏőœŕŗřśŝşšţťŧũūŭů"
    "űųŵŷźżžſƀƃƅƈƌƍƒƕƙƚƛƞơƣƥƨƪƫƭưƴƶƹƺƽƾƿǆǉǌǎǐǒǔǖǘǚǜǝǟǡǣǥǧǩǫǭǯǰǳǵǹǻǽǿȁȃȅȇȉȋȍȏȑȓȕȗșțȝȟȡȣȥȧȩȫȭȯȱȳȴȵ"
    "ȶȸȹȼȿɀɂɇɉɋɍɏɐɑɒɓɔɕɖɗɘəɚɛɜɝɞɟɠɡɢɣɤɥɦɧɨɩɪɫɬɭɮɯɰɱɲɳɴɵɶɷɸɹɺɻɼɽɾɿʀʁʂʃʄʅʆʇʈʉʊʋʌʍʎʏʐʑʒʓʕʖʗʘʙʚʛʜʝʞʟʠʡʢ"
    "ʣʤʥʦʧʨʩʪʫʬʭʮʯͻͼͽΐάέήίΰαβγδεζηθικλμνξοπρςστυφχψωϊϋόύώϐϑϕϖϗϙϛϝϟϡϣϥϧϩϫϭϯϰϱϲϳϵϸϻϼабвгдежзийклмноп"
    "рстуфхцчшщъыьэюяѐёђѓєѕіїјљњћќѝўџѡѣѥѧѩѫѭѯѱѳѵѷѹѻѽѿҁҋҍҏґғҕҗҙқҝҟҡңҥҧҩҫҭүұҳҵҷҹһҽҿӂӄӆӈӊӌӎӏӑӓӕ"
    "ӗәӛӝӟӡӣӥӧөӫӭӯӱӳӵӷӹӻӽӿԁԃԅԇԉԋԍԏԑԓԛԝաբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆևᴀᴁᴂᴃᴄᴅᴆᴇᴈᴉᴊᴋᴌᴍᴎᴏᴐᴑᴒ"
    "ᴓᴔᴕᴖᴗᴘᴙᴚᴛᴜᴝᴞᴟᴠᴡᴢᴣᴤᴥᴦᴧᴨᴩᴪᴫᵫᵬᵭᵮᵯᵰᵱᵲᵳᵴᵵᵶᵷᵹᵺᵻᵼᵽᵾᵿᶀᶁᶂᶃᶄᶅᶆᶇᶈᶉᶊᶋᶌᶍᶎᶏᶐᶑᶒᶓᶔᶕᶖᶗᶘᶙᶚḁḃḅḇḉḋḍḏḑḓḕḗḙḛḝḟḡḣḥḧḩ"
    "ḫḭḯḱḳḵḷḹḻḽḿṁṃṅṇṉṋṍṏṑṓṕṗṙṛṝṟṡṣṥṧṩṫṭṯṱṳṵṷṹṻṽṿẁẃẅẇẉẋẍẏẑẓẕẗẘẙẚẛạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợ"
    "ụủứừửữựỳỵỷỹἀἁἂἃἄἅἆἇἐἑἒἓἔἕἠἡἢἣἤἥἦἧἰἱἲἳἴἵἶἷὀὁὂὃὄὅὐὑὒὓὔὕὖὗὠὡὢὣὤὥὦὧὰάὲέὴήὶίὸόὺύὼώᾀᾁᾂᾃᾄᾅᾆᾇᾐᾑᾒᾓᾔᾕᾖᾗ"
    "ᾠᾡᾢᾣᾤᾥᾦᾧᾰᾱᾲᾳᾴᾶᾷιῂῃῄῆῇῐῑῒΐῖῗῠῡῢΰῤῥῦῧῲῳῴῶῷℓⅎↄⱡⱥⱦⱨⱪⱬⱱⱳⱴⱶⱷ"
)
UNICODE_UPPERS = (
    "A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞĀĂĄĆĈĊČĎĐĒĔĖĘĚĜĞĠĢĤĦĨĪĬĮİĲĴĶĹĻĽĿŁŃŅŇŊŌŎŐŒŔŖŘŚŜŞŠŢŤŦŨŪŬŮŰŲŴŶŸ"
    "ŹŻŽƁƂƄƆƇƉƊƋƎƏƐƑƓƔƖƗƘƜƝƟƠƢƤƦƧƩƬƮƯƱƲƳƵƷƸƼǄǇǊǍǏǑǓǕǗǙǛǞǠǢǤǦǨǪǬǮǱǴǶǷǸǺǼǾȀȂȄȆȈȊȌȎȐȒȔȖȘȚȜȞȠȢȤȦȨȪȬȮȰȲ"
    "ȺȻȽȾɁɃɄɅɆɈɊɌɎΆΈΉΊΌΎΏΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩΪΫϏϒϓϔϘϚϜϞϠϢϤϦϨϪϬϮϴϷϹϺϽϾϿЀЁЂЃЄЅІЇЈЉЊЋЌЍЎЏАБВГДЕЖЗ"
    "ИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯѠѢѤѦѨѪѬѮѰѲѴѶѸѺѼѾҀҊҌҎҐҒҔҖҘҚҜҞҠҢҤҦҨҪҬҮҰҲҴҶҸҺҼҾӀӁӃӅӇӉӋӍӐӒӔӖӘӚӜӞӠӢӤӦӨӪӬӮӰ"
    "ӲӴӶӸӺӼӾԀԂԄԆԈԊԌԎԐԒԚԜԱԲԳԴԵԶԷԸԹԺԻԼԽԾԿՀՁՂՃՄՅՆՇՈՉՊՋՌՍՎՏՐՑՒՓՔՕՖᎠᎡᎢᎣᎤᎥᎦᎧᎨᎩᎪᎫᎬᎭᎮᎯᎰᎱᎲᎳᎴᎵᎶᎷᎸᎹᎺᎻᎼᎽᎾᎿᏀᏁᏂᏃ"
    "ᏄᏅᏆᏇᏈᏉᏊᏋᏌᏍᏎᏏᏐᏑᏒᏓᏔᏕᏖᏗᏘᏙᏚᏛᏜᏝᏞᏟᏠᏡᏢᏣᏤᏥᏦᏧᏨᏩᏪᏫᏬᏭᏮᏯᏰᏱᏲᏳᏴᏵḀḂḄḆḈḊḌḎḐḒḔḖḘḚḜḞḠḢḤḦḨḪḬḮḰḲḴḶḸḺḼḾṀṂṄṆṈṊṌṎṐṒṔ"
    "ṖṘṚṜṞṠṢṤṦṨṪṬṮṰṲṴṶṸṺṼṾẀẂẄẆẈẊẌẎẐẒẔẞẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸἈἉἊἋἌἍἎἏἘἙἚἛἜἝἨ"
    "ἩἪἫἬἭἮἯἸἹἺἻἼἽἾἿὈὉὊὋὌὍὙὛὝὟὨὩὪὫὬὭὮὯᾸᾹᾺΆῈΈῊΉῘῙῚΊῨῩῪΎῬῸΌῺΏⱠⱢⱣⱤⱧⱩⱫⱭⱲⱵＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ𐐀𐐁𐐂"
    "𐐃𐐄𐐅𐐆𐐇𐐈𐐉𐐊𐐋𐐌𐐍𐐎𐐏𐐐𐐑𐐒𐐓𐐔𐐕𐐖𐐗𐐘𐐙𐐚𐐛𐐜𐐝𐐞𐐟𐐠𐐡𐐢𐐣𐐤𐐥𐐦𐐧"
)
UNICODE_DIGITS = "0-9"
UNICODE_PUNCTS = (
    "-֊־᠆‒–—―⸗〜〰゠︱﹣－_︳︴﹍﹎﹏＿\\)\\]\\}᚜〉》」』】〕〗〙〛〞〟﴾︘︶︸︺︼︾﹀﹂﹄﹚﹜﹞）］｝｠｣\\(\\[\\{᚛‚„〈《「『【〔〖〘〚〝﴿︗︵︷︹︻︽︿﹁﹃"
    "﹙﹛﹝（［｛｟｢!\"#%&'*,./:;?@\\\\¡§¶·¿;·՚՛՜՝՞՟։׀׃׆׳״،؍؛؞؟٪٫٬٭۔܀܁܂܃܄܅܆܇܈܉܊܋܌܍߷߸߹।॥॰෴๏๚๛༄༅༆༇༈༉༊་༌།༎༏༐"
    "༑༒༔྅࿐࿑࿒࿓࿔჻፠፡።፣፤፥፦፧፨᙭᙮᛫᛬᛭។៕៖៘៙៚᠀᠁᠂᠃᠄᠅᠇᠈᠉᠊‗†‡•…‰′″‴※‼‾⁞、。〃〽・꘍꘎꘏꡴꡵꡶꡷︐︑︒︓︔︕︖︙︰﹅﹆﹉﹊﹋﹌﹐﹑﹒﹔﹕﹖﹗﹟﹠﹡﹨﹪﹫"
    "！＂＃％＆＇＊，．／：；？＠＼｡､･«»•"
)
UNICODE_ALPHAS = UNICODE_LOWERS + UNICODE_UPPERS
UNICODE_ALPHANUMS = UNICODE_ALPHAS + UNICODE_DIGITS


class Pattern:
    def __init__(self, case_insensitive=False, *args):
        self._case_insensitive = case_insensitive
        pass

    def instanciate(self, matrix, index):
        raise RuntimeError("undefined")


class ConstantPattern(Pattern):
    def __init__(self, value, case_insensitive=False, *args):
        self._value = value

    def __str__(self):
        return self._value

    def instanciate(self, matrix, index):
        return self._value

    @property
    def value(self):
        return self._value


class IdentityPattern(Pattern):
    __pattern = re.compile("%x\\[(-?[0-9]+),([0-9]+)\\]")

    def __init__(self, x, y, case_insensitive=False, column=None, *args):
        self._x = x
        self._y = y
        self._column = column

    def __str__(self):
        return "%x[{p.x},{p.y}]".format(p=self)

    def instanciate(self, matrix, index):
        x = index + self.x
        if x < 0:
            if x > -5:
                return "_x{0:+d}".format(x)
            else:
                return "_x-#"
        if x >= len(matrix):
            diff = x - len(matrix) + 1
            if diff < 5:
                return "_x{0:+d}".format(diff)
            else:
                return "_x+#"

        return str(matrix[x][self.y])

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def column(self):
        return self._column

    @classmethod
    def from_string(cls, string, case_insensitive=False, column=None):
        match = cls.__pattern.search(string)
        groups = match.groups()
        return IdentityPattern(
            int(groups[0]), int(groups[1]), case_insensitive=case_insensitive, column=column
        )


class RegexPattern(IdentityPattern):
    __sub = {
        "\\l": "[{0}]".format(UNICODE_LOWERS),
        "\\L": "[^{0}]".format(UNICODE_LOWERS),
        "\\u": "[{0}]".format(UNICODE_UPPERS),
        "\\U": "[^{0}]".format(UNICODE_UPPERS),
        "\\d": "[{0}]".format(UNICODE_DIGITS),
        "\\D": "[^{0}]".format(UNICODE_DIGITS),
        "\\p": "[{0}]".format(UNICODE_PUNCTS),
        "\\P": "[^{0}]".format(UNICODE_PUNCTS),
        "\\a": "[{0}]".format(UNICODE_ALPHAS),
        "\\A": "[^{0}]".format(UNICODE_ALPHAS),
        "\\w": "[{0}]".format(UNICODE_ALPHANUMS),
        "\\W": "[^{0}]".format(UNICODE_ALPHANUMS),
    }

    def __init__(self, x, y, pattern, case_insensitive=False, *args):
        super(RegexPattern, self).__init__(x, y, *args)
        self._pattern = pattern
        for key, value in RegexPattern.__sub.items():
            self._pattern = self._pattern.replace(key, value)
        self._pattern = re.compile(self._pattern, re.U + re.M)

    @classmethod
    def sub(cls):
        return RegexPattern.__sub

    """def instanciate(self, matrix, index):
        cell = super(RegexPattern, self).instanciate(matrix, index)

        return self._pattern.search(cell)"""


class TestPattern(RegexPattern):
    __pattern = re.compile(r'%t\[\s*(-?[0-9]+),([0-9]+),"(.+)"\]', re.I)

    def __str__(self):
        p = self._pattern.pattern[:]
        for x, y in RegexPattern.sub().items():
            p = p.replace(y, x)
        return '%t[{p.x},{p.y},"{pat}"]'.format(p=self, pat=p)

    def instanciate(self, matrix, index, case_insensitive=False):
        cell = super(TestPattern, self).instanciate(matrix, index)

        return (self._pattern.search(cell) is not None).lower()

    @classmethod
    def from_string(cls, string, case_insensitive=False, column=None):
        match = cls.__pattern.search(string)
        groups = match.groups()
        return TestPattern(
            int(groups[0]), int(groups[1]), groups[2], case_insensitive=case_insensitive
        )


class MatchPattern(RegexPattern):
    __pattern = re.compile(r'%m\[\s*(-?[0-9]+),([0-9]+),"([^"]+?)"\]', re.I)

    def __str__(self):
        p = self._pattern.pattern[:]
        for x, y in RegexPattern.sub().items():
            p = p.replace(y, x)
        return '%m[{p.x},{p.y},"{pat}"]'.format(p=self, pat=p)

    def instanciate(self, matrix, index, case_insensitive=False):
        cell = super(MatchPattern, self).instanciate(matrix, index)

        cell = self._pattern.search(cell)
        if cell is None:
            return ""

        return cell.group()

    @classmethod
    def from_string(cls, string, case_insensitive=False, column=None):
        match = cls.__pattern.search(string)
        groups = match.groups()
        return MatchPattern(
            int(groups[0]), int(groups[1]), groups[2], case_insensitive=case_insensitive
        )


class ListPattern(Pattern):
    __pattern = re.compile(r'%[xtm]\[\s*-?[0-9]+,-?[0-9]+(,".+?")?\]', re.I)

    def __init__(self, patterns):
        self._patterns = patterns[:]
        self._instanciators = [pattern.instanciate for pattern in self._patterns]

    def __str__(self):
        return "".join([str(p) for p in self._patterns])

    @property
    def patterns(self):
        return self._patterns

    def instanciate(self, matrix, index):
        return "".join([instanciator(matrix, index) for instanciator in self._instanciators])

    @classmethod
    def from_string(cls, string, case_insensitive=False, column=None):
        patterns = []
        prev = 0
        finding = None
        for finding in cls.__pattern.finditer(string):
            patterns.append(pattern_factory(string[prev: finding.start()]))
            patterns.append(pattern_factory(string[finding.start(): finding.end()]))
            prev = finding.end()
        if finding is None:
            patterns.append(ConstantPattern(string))
        elif string[prev:]:
            patterns.append(ConstantPattern(string[prev:]))
        return ListPattern(patterns)


def pattern_factory(string):
    if string.startswith("%x"):
        return IdentityPattern.from_string(
            string, case_insensitive=string[1].isupper(), column=None
        )
    elif string.startswith("%t"):
        return TestPattern.from_string(string, case_insensitive=string[1].isupper(), column=None)
    elif string.startswith("%m"):
        return MatchPattern.from_string(string, case_insensitive=string[1].isupper(), column=None)
    return ConstantPattern(string)


class Quark:
    def __init__(self):
        self._encoder = {}
        self._decoder = []

    def __len__(self):
        return len(self._decoder)

    def __iter__(self):
        return iter(self._decoder[:])

    def __contains__(self, element):
        return element in self._encoder

    def keys(self):
        return self._decoder[:]

    def add(self, element, strict=False):
        if element not in self._encoder:
            self._encoder[element] = len(self)
            self._decoder.append(element)
        elif strict:
            raise KeyError("'{0}' already in coder".format(element))

    def insert(self, index, element):
        if element not in self._encoder:
            self._decoder.insert(index, element)
            self._encoder[element] = index
            for nth in range(index + 1, len(self._encoder)):
                self._encoder[self._decoder[nth]] = nth

    def encode(self, element):
        return self._encoder.get(element, -1)

    def decode(self, integer):
        try:
            return self._decoder[integer]
        except Exception:
            return None


class Model:
    def __init__(self, constraints={}):
        self._tagset = Quark()
        self._templates = []
        self._observations = Quark()
        self._uoff = []
        self._boff = []
        self._weights = []  # list
        self._max_col = 0

    def __call__(self, x):
        return self.tag_viterbi(x)

    @classmethod
    def from_wapiti_model(cls, filename, encoding="utf-8", verbose=True):
        model = Model()
        n_weights = -1
        n_patterns = -1
        n_labels = -1
        n_observations = -1
        current_feature = 0
        line_index = 0
        mode = ("rb" if encoding is None else "r")
        with open(filename, mode, encoding=encoding) as input_stream:
            lines = [line.strip() for line in input_stream]

        n_weights = int(lines[line_index].split("#")[-1])
        line_index += 1

        n_patterns, max_col, other = lines[line_index].split("#")[-1].split("/")
        n_patterns = int(n_patterns)
        max_col = int(max_col)
        model._max_col = max_col
        line_index += 1

        for line in lines[line_index: line_index + n_patterns]:
            line = line.split(":", 1)[1][:-1]
            model._templates.append(ListPattern.from_string(line))
        assert len(model.templates) == n_patterns
        line_index += n_patterns

        # labels
        n_labels = int(lines[line_index].strip().split("#")[-1])
        line_index += 1
        for line in lines[line_index: line_index + n_labels]:
            line = line.strip()
            model.tagset.add(line[line.index(":") + 1: -1])
        line_index += n_labels
        assert len(model.tagset) == n_labels

        # observations
        n_observations = int(lines[line_index].split("#")[-1])
        line_index += 1
        model._uoff = [-1] * n_observations
        model._boff = [-1] * n_observations
        for line in lines[line_index: line_index + n_observations]:
            obs = line[line.index(":") + 1: -1]
            n_feats = n_labels if obs[0] in "u*" else 0
            n_feats += n_labels ** 2 if obs[0] in "b*" else 0

            model.observations.add(obs)
            if obs[0] in "u*":
                model.uoff[len(model.observations) - 1] = current_feature
            if obs[0] in "b*":
                model.boff[len(model.observations) - 1] = current_feature
                +(n_labels if obs[0] == "*" else 0)
            current_feature += n_feats
        line_index += n_observations
        model._weights = [0.0] * current_feature

        # features
        for line in lines[-n_weights:]:
            index, weight = line.split("=")
            model.weights[int(index)] = float.fromhex(weight)

        return model

    @property
    def tagset(self):
        return self._tagset

    @property
    def templates(self):
        return self._templates

    @property
    def observations(self):
        return self._observations

    @property
    def uoff(self):
        """Unigram OFFset"""
        return self._uoff

    @property
    def boff(self):
        """Bigram OFFset"""
        return self._boff

    @property
    def weights(self):
        return self._weights

    def tag_viterbi(self, sentence):
        Y = len(self.tagset)
        T = len(sentence)
        range_Y = range(Y)
        range_T = range(T)
        psi = [[[0.0] * Y for _y1 in range_Y] for _t in range_T]
        back = [[0] * Y for _t in range_T]
        cur = [0.0] * Y
        old = [0.0] * Y
        psc = [0.0] * T
        sc = -2 ** 30
        tag = ["" for _t in range_T]
        # avoiding dots
        weights_ = self._weights
        obs_encode = self._observations.encode
        templates_ = self._templates
        uoff_ = self._uoff
        boff_ = self._boff

        unigrams = []
        bigrams = []
        for t in range_T:
            unigrams.append([])
            bigrams.append([])
            u_append = unigrams[-1].append
            b_append = bigrams[-1].append
            for template in templates_:
                obs = template.instanciate(sentence, t)
                o = obs_encode(obs)
                if o != -1:
                    if obs[0] == "u" and uoff_[o] != -1:
                        u_append(weights_[uoff_[o]: uoff_[o] + Y])
                    if obs[0] == "b" and boff_[o] != -1:
                        b_append(weights_[boff_[o]: boff_[o] + Y * Y])

        # compute scores in psi
        for t in range_T:
            unigrams_T = unigrams[t]
            for y in range_Y:
                sum_ = 0.0
                for w in unigrams_T:
                    sum_ += w[y]
                for yp in range_Y:
                    psi[t][yp][y] = sum_
        for t in range(1, T):
            bigrams_T = bigrams[t]
            d = 0
            for yp, y in itertools.product(range_Y, range_Y):
                for w in bigrams_T:
                    psi[t][yp][y] += w[d]
                d += 1

        for y in range_Y:
            cur[y] = psi[0][0][y]
        for t in range(1, T):
            for y in range_Y:
                old[y] = cur[y]
            for y in range_Y:
                bst = -2 ** 30
                idx = 0
                for yp in range_Y:
                    val = old[yp] + psi[t][yp][y]
                    if val > bst:
                        bst = val
                        idx = yp
                back[t][y] = idx
                cur[y] = bst

        bst = 0
        for y in range(1, Y):
            if cur[y] > cur[bst]:
                bst = y
        sc = cur[bst]
        for t in reversed(range_T):
            yp = back[t][bst] if t != 0 else 0
            y = bst
            tag[t] = self._tagset.decode(y)
            psc[t] = psi[t][yp][y]
            bst = yp

        return tag, psc, sc

    def write(self, filename, encoding="utf-8"):
        with open(filename, "w", encoding=encoding, newline="") as output_stream:
            output_stream.write("#mdl#2#{0}\n".format(len([w for w in self.weights if w != 0.0])))
            output_stream.write("#rdr#{0}/{1}/0\n".format(len(self._templates), self._max_col))
            for pattern in self._templates:
                uni_pattern = str(pattern)
                output_stream.write("{0}:{1},\n".format(len(uni_pattern), uni_pattern))
            output_stream.write("#qrk#{0}\n".format(len(self._tagset)))
            for tag in self.tagset:
                output_stream.write("{0}:{1}\n".format(len(tag), tag))
            # observations
            output_stream.write("#qrk#{0}\n".format(len(self._observations)))
            for obs in self._observations:
                output_stream.write("{0}:{1}\n".format(len(obs), obs))
            for index, w in enumerate(self.weights):
                if w != 0.0:
                    output_stream.write("{0}={1}\n".format(index, float.hex(w)))

    def dump(self, filename):
        ntags = len(self.tagset)
        with open(filename, "w", encoding="utf-8", newline="") as output_stream:
            for i in range(len(self.observations)):
                o = self.observations.decode(i)
                written = False
                if o[0] == "u":
                    off = self.uoff[i]
                    for y in range(ntags):
                        w = self.weights[off + y]
                        if w != 0:
                            output_stream.write(
                                "{0}\t{1}\t{2}\t{3:.5f}\n".format(o, "#", self.tagset.decode(y), w)
                            )
                            written = True
                else:
                    off = self.boff[i]
                    d = 0
                    for yp in range(ntags):
                        for y in range(ntags):
                            w = self.weights[off + d]
                            if w != 0:
                                output_stream.write(
                                    "{0}\t{1}\t{2}\t{3:.5f}\n".format(
                                        o, self.tagset.decode(yp), self.tagset.decode(y), w
                                    )
                                )
                                written = True
                            d += 1
                if written:
                    output_stream.write("\n")
