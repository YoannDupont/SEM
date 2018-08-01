#-*- coding:utf-8-*-

"""
file: template.py

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

UNICODE_LOWERS = u"a-zµßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿāăąćĉċčďđēĕėęěĝğġģĥħĩīĭįıĳĵķĸĺļľŀłńņňŉŋōŏőœŕŗřśŝşšţťŧũūŭůűųŵŷźżžſƀƃƅƈƌƍƒƕƙƚƛƞơƣƥƨƪƫƭưƴƶƹƺƽƾƿǆǉǌǎǐǒǔǖǘǚǜǝǟǡǣǥǧǩǫǭǯǰǳǵǹǻǽǿȁȃȅȇȉȋȍȏȑȓȕȗșțȝȟȡȣȥȧȩȫȭȯȱȳȴȵȶȸȹȼȿɀɂɇɉɋɍɏɐɑɒɓɔɕɖɗɘəɚɛɜɝɞɟɠɡɢɣɤɥɦɧɨɩɪɫɬɭɮɯɰɱɲɳɴɵɶɷɸɹɺɻɼɽɾɿʀʁʂʃʄʅʆʇʈʉʊʋʌʍʎʏʐʑʒʓʕʖʗʘʙʚʛʜʝʞʟʠʡʢʣʤʥʦʧʨʩʪʫʬʭʮʯͻͼͽΐάέήίΰαβγδεζηθικλμνξοπρςστυφχψωϊϋόύώϐϑϕϖϗϙϛϝϟϡϣϥϧϩϫϭϯϰϱϲϳϵϸϻϼабвгдежзийклмнопрстуфхцчшщъыьэюяѐёђѓєѕіїјљњћќѝўџѡѣѥѧѩѫѭѯѱѳѵѷѹѻѽѿҁҋҍҏґғҕҗҙқҝҟҡңҥҧҩҫҭүұҳҵҷҹһҽҿӂӄӆӈӊӌӎӏӑӓӕӗәӛӝӟӡӣӥӧөӫӭӯӱӳӵӷӹӻӽӿԁԃԅԇԉԋԍԏԑԓԛԝաբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆևᴀᴁᴂᴃᴄᴅᴆᴇᴈᴉᴊᴋᴌᴍᴎᴏᴐᴑᴒᴓᴔᴕᴖᴗᴘᴙᴚᴛᴜᴝᴞᴟᴠᴡᴢᴣᴤᴥᴦᴧᴨᴩᴪᴫᵫᵬᵭᵮᵯᵰᵱᵲᵳᵴᵵᵶᵷᵹᵺᵻᵼᵽᵾᵿᶀᶁᶂᶃᶄᶅᶆᶇᶈᶉᶊᶋᶌᶍᶎᶏᶐᶑᶒᶓᶔᶕᶖᶗᶘᶙᶚḁḃḅḇḉḋḍḏḑḓḕḗḙḛḝḟḡḣḥḧḩḫḭḯḱḳḵḷḹḻḽḿṁṃṅṇṉṋṍṏṑṓṕṗṙṛṝṟṡṣṥṧṩṫṭṯṱṳṵṷṹṻṽṿẁẃẅẇẉẋẍẏẑẓẕẗẘẙẚẛạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹἀἁἂἃἄἅἆἇἐἑἒἓἔἕἠἡἢἣἤἥἦἧἰἱἲἳἴἵἶἷὀὁὂὃὄὅὐὑὒὓὔὕὖὗὠὡὢὣὤὥὦὧὰάὲέὴήὶίὸόὺύὼώᾀᾁᾂᾃᾄᾅᾆᾇᾐᾑᾒᾓᾔᾕᾖᾗᾠᾡᾢᾣᾤᾥᾦᾧᾰᾱᾲᾳᾴᾶᾷιῂῃῄῆῇῐῑῒΐῖῗῠῡῢΰῤῥῦῧῲῳῴῶῷℓⅎↄⱡⱥⱦⱨⱪⱬⱱⱳⱴⱶⱷ"
UNICODE_UPPERS = u"A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞĀĂĄĆĈĊČĎĐĒĔĖĘĚĜĞĠĢĤĦĨĪĬĮİĲĴĶĹĻĽĿŁŃŅŇŊŌŎŐŒŔŖŘŚŜŞŠŢŤŦŨŪŬŮŰŲŴŶŸŹŻŽƁƂƄƆƇƉƊƋƎƏƐƑƓƔƖƗƘƜƝƟƠƢƤƦƧƩƬƮƯƱƲƳƵƷƸƼǄǇǊǍǏǑǓǕǗǙǛǞǠǢǤǦǨǪǬǮǱǴǶǷǸǺǼǾȀȂȄȆȈȊȌȎȐȒȔȖȘȚȜȞȠȢȤȦȨȪȬȮȰȲȺȻȽȾɁɃɄɅɆɈɊɌɎΆΈΉΊΌΎΏΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩΪΫϏϒϓϔϘϚϜϞϠϢϤϦϨϪϬϮϴϷϹϺϽϾϿЀЁЂЃЄЅІЇЈЉЊЋЌЍЎЏАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯѠѢѤѦѨѪѬѮѰѲѴѶѸѺѼѾҀҊҌҎҐҒҔҖҘҚҜҞҠҢҤҦҨҪҬҮҰҲҴҶҸҺҼҾӀӁӃӅӇӉӋӍӐӒӔӖӘӚӜӞӠӢӤӦӨӪӬӮӰӲӴӶӸӺӼӾԀԂԄԆԈԊԌԎԐԒԚԜԱԲԳԴԵԶԷԸԹԺԻԼԽԾԿՀՁՂՃՄՅՆՇՈՉՊՋՌՍՎՏՐՑՒՓՔՕՖᎠᎡᎢᎣᎤᎥᎦᎧᎨᎩᎪᎫᎬᎭᎮᎯᎰᎱᎲᎳᎴᎵᎶᎷᎸᎹᎺᎻᎼᎽᎾᎿᏀᏁᏂᏃᏄᏅᏆᏇᏈᏉᏊᏋᏌᏍᏎᏏᏐᏑᏒᏓᏔᏕᏖᏗᏘᏙᏚᏛᏜᏝᏞᏟᏠᏡᏢᏣᏤᏥᏦᏧᏨᏩᏪᏫᏬᏭᏮᏯᏰᏱᏲᏳᏴᏵḀḂḄḆḈḊḌḎḐḒḔḖḘḚḜḞḠḢḤḦḨḪḬḮḰḲḴḶḸḺḼḾṀṂṄṆṈṊṌṎṐṒṔṖṘṚṜṞṠṢṤṦṨṪṬṮṰṲṴṶṸṺṼṾẀẂẄẆẈẊẌẎẐẒẔẞẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸἈἉἊἋἌἍἎἏἘἙἚἛἜἝἨἩἪἫἬἭἮἯἸἹἺἻἼἽἾἿὈὉὊὋὌὍὙὛὝὟὨὩὪὫὬὭὮὯᾸᾹᾺΆῈΈῊΉῘῙῚΊῨῩῪΎῬῸΌῺΏⱠⱢⱣⱤⱧⱩⱫⱭⱲⱵＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ𐐀𐐁𐐂𐐃𐐄𐐅𐐆𐐇𐐈𐐉𐐊𐐋𐐌𐐍𐐎𐐏𐐐𐐑𐐒𐐓𐐔𐐕𐐖𐐗𐐘𐐙𐐚𐐛𐐜𐐝𐐞𐐟𐐠𐐡𐐢𐐣𐐤𐐥𐐦𐐧"
UNICODE_DIGITS = u"0-9"
UNICODE_PUNCTS = u"-֊־᠆‒–—―⸗〜〰゠︱﹣－_︳︴﹍﹎﹏＿\\)\\]\\}᚜〉》」』】〕〗〙〛〞〟﴾︘︶︸︺︼︾﹀﹂﹄﹚﹜﹞）］｝｠｣\\(\\[\\{᚛‚„〈《「『【〔〖〘〚〝﴿︗︵︷︹︻︽︿﹁﹃﹙﹛﹝（［｛｟｢!\"#%&'*,./:;?@\\\\¡§¶·¿;·՚՛՜՝՞՟։׀׃׆׳״،؍؛؞؟٪٫٬٭۔܀܁܂܃܄܅܆܇܈܉܊܋܌܍߷߸߹।॥॰෴๏๚๛༄༅༆༇༈༉༊་༌།༎༏༐༑༒༔྅࿐࿑࿒࿓࿔჻፠፡።፣፤፥፦፧፨᙭᙮᛫᛬᛭។៕៖៘៙៚᠀᠁᠂᠃᠄᠅᠇᠈᠉᠊‗†‡•…‰′″‴※‼‾⁞、。〃〽・꘍꘎꘏꡴꡵꡶꡷︐︑︒︓︔︕︖︙︰﹅﹆﹉﹊﹋﹌﹐﹑﹒﹔﹕﹖﹗﹟﹠﹡﹨﹪﹫！＂＃％＆＇＊，．／：；？＠＼｡､･«»•"
UNICODE_ALPHAS = UNICODE_LOWERS + UNICODE_UPPERS
UNICODE_ALPHANUMS = UNICODE_ALPHAS + UNICODE_DIGITS

class Pattern(object):
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
    
    def __unicode__(self):
        return self._value
    
    def instanciate(self, matrix, index):
        return self._value
    
    @property
    def value(self):
        return self._value

class IdentityPattern(Pattern):
    __pattern = re.compile(u"%x\\[(-?[0-9]+),([0-9]+)\\]")
    
    def __init__(self, x, y, case_insensitive=False, column=None, *args):
        self._x = x
        self._y = y
        self._column = column
    
    def __str__(self):
        return '%x[{p.x},{p.y}]'.format(p=self)
    
    def __unicode__(self):
        return u'%x[{p.x},{p.y}]'.format(self.x, self.y)
    
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
                return u"_x+#"
        
        return unicode(matrix[x][self.y])
    
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
        return IdentityPattern(int(groups[0]),int(groups[1]), case_insensitive=case_insensitive, column=column)

class RegexPattern(IdentityPattern):
    __sub = {u"\\l":u"[{0}]".format(UNICODE_LOWERS),
             u"\\L":u"[^{0}]".format(UNICODE_LOWERS),
             u"\\u":u"[{0}]".format(UNICODE_UPPERS),
             u"\\U":u"[^{0}]".format(UNICODE_UPPERS),
             u"\\d":u"[{0}]".format(UNICODE_DIGITS),
             u"\\D":u"[^{0}]".format(UNICODE_DIGITS),
             u"\\p":u"[{0}]".format(UNICODE_PUNCTS),
             u"\\P":u"[^{0}]".format(UNICODE_PUNCTS),
             u"\\a":u"[{0}]".format(UNICODE_ALPHAS),
             u"\\A":u"[^{0}]".format(UNICODE_ALPHAS),
             u"\\w":u"[{0}]".format(UNICODE_ALPHANUMS),
             u"\\W":u"[^{0}]".format(UNICODE_ALPHANUMS)
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
    __pattern = re.compile('%t\\[\s*(-?[0-9]+),([0-9]+),"(.+)"\\]', re.I)
    
    def __str__(self):
        p = self._pattern.pattern[:]
        for x,y in RegexPattern.sub().items():
            p = p.replace(y, x)
        return u'%t[{p.x},{p.y},"{pat}"]'.format(p=self, pat=p)
    
    def __unicode__(self):
        p = self._pattern.pattern[:]
        for x,y in RegexPattern.sub().items():
            p = p.replace(y, x)
        return u'%t[{p.x},{p.y},"{pat}"]'.format(p=self, pat=p)
    
    def instanciate(self, matrix, index, case_insensitive=False):
        cell = super(TestPattern, self).instanciate(matrix, index)
        
        return unicode(self._pattern.search(cell) is not None).lower()
    
    @classmethod
    def from_string(cls, string, case_insensitive=False, column=None):
        match = cls.__pattern.search(string)
        groups = match.groups()
        return TestPattern(int(groups[0]),int(groups[1]),groups[2], case_insensitive=case_insensitive)

class MatchPattern(RegexPattern):
    __pattern = re.compile('%m\\[\s*(-?[0-9]+),([0-9]+),"([^"]+?)"\\]', re.I)
    
    def __str__(self):
        p = self._pattern.pattern[:]
        for x,y in RegexPattern.sub().items():
            p = p.replace(y, x)
        return u'%m[{p.x},{p.y},"{pat}"]'.format(p=self, pat=p)
    
    def __unicode__(self):
        p = self._pattern.pattern[:]
        for x,y in RegexPattern.sub().items():
            p = p.replace(y, x)
        return u'%m[{p.x},{p.y},"{pat}"]'.format(p=self, pat=p)
    
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
        return MatchPattern(int(groups[0]),int(groups[1]),groups[2], case_insensitive=case_insensitive)

class ListPattern(Pattern):
    __pattern = re.compile(r'%[xtm]\[\s*-?[0-9]+,-?[0-9]+(,".+?")?\]', re.I)
    
    def __init__(self, patterns):
        self._patterns = patterns[:]
        self._instanciators = [pattern.instanciate for pattern in self._patterns]
    
    def __str__(self):
        return ''.join([str(p) for p in self._patterns])
    
    def __unicode__(self):
        return u''.join([unicode(p) for p in self._patterns])
    
    @property
    def patterns(self):
        return self._patterns
    
    def instanciate(self, matrix, index):
        return u"".join([instanciator(matrix, index) for instanciator in self._instanciators])
    
    @classmethod
    def from_string(cls, string, case_insensitive=False, column=None):
        patterns = []
        prev = 0
        finding = None
        for finding in cls.__pattern.finditer(string):
            patterns.append(pattern_factory(string[prev : finding.start()]))
            patterns.append(pattern_factory(string[finding.start() : finding.end()]))
            prev = finding.end()
        if finding is None:
            patterns.append(ConstantPattern(string))
        elif string[prev:]:
            patterns.append(ConstantPattern(string[prev : ]))
        return ListPattern(patterns)

def pattern_factory(string):
    low = string.lower()
    if string.startswith("%x"):
        return IdentityPattern.from_string(string, case_insensitive=string[1].isupper(), column=None)
    elif string.startswith("%t"):
        return TestPattern.from_string(string, case_insensitive=string[1].isupper(), column=None)
    elif string.startswith("%m"):
        return MatchPattern.from_string(string, case_insensitive=string[1].isupper(), column=None)
    return ConstantPattern(string)
