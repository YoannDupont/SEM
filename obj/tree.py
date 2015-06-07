import re, cPickle

from os.path import join, abspath, dirname
    
class Node(object):
    def __init__(self, entry):
        self.entry  = entry
        self.parent = None
        self.value  = None
        self.shift  = None
    
    @staticmethod
    def get_shift(node):
        return int(node.attrib["x"]) if "x" in node.attrib else 0
    
    def get_entry(self, node):
        return node.attrib["entry"] if "entry" in node.attrib else self.entry
    
    @staticmethod
    def str_to_boolean(s):
        return {"false":False,"true":True}[s.lower()]
    
    @staticmethod
    def returns_boolean(node):
        # coded this way for better readability, as this does not need to be
        # fast, but may be expanded again and again.
        if isinstance(node, BooleanNode):
            return True
        elif isinstance(node, ListNode):
            return True
        elif isinstance(node, RegexpNode):
            return node.value == "check"
        return False
    
    def parse(self, elt, parent):
        raise RuntimeError("parse undefined for root type Node.")
    
    def eval(self, sentdict, position):
        raise RuntimeError("eval undefined for root type Node.")


class NaryNode(Node):
    def __init__(self, column):
        super(NaryNode, self).__init__(column)
        self.arity = None
    
    def parse(self, elt, parent):
        self.arity  = elt.tag.lower()
        self.action = elt.attrib["action"].lower()
        self.shift  = Node.get_shift(elt)
        self.entry  = self.get_entry(elt)
        
        if self.arity == "nullary":
            if self.action not in ("lower", "upper", "degenerate"):
                raise RuntimeError("Unknown action: %s" %self.action)
        elif self.arity == "nary":
            if self.action == "substitute":
                self.value = []
                to_parse   = elt.getchildren()
                assert (len(to_parse) % 2 == 0)
                i = 0
                while i < len(to_parse):
                    assert (to_parse[i].tag.lower() == "pattern" and to_parse[i+1].tag.lower() == "replace")
                    self.value.append([re.compile(to_parse[i].text, re.M + re.U), (to_parse[i+1].text if to_parse[i+1].text is not None else "")])
                    i += 2
            else:
                raise RuntimeError("Unknown action: %s" %self.action)
        else:
            raise RuntimeError("Unknown arity: %s" %self.arity)
    
    def eval(self, sentdict, position):
        def evaluate():
            index = position + self.shift
            entry = self.entry
            if index < 0 or index >= len(sentdict):
                return "_null_"
            
            token = sentdict[index][entry]
            if self.arity == "nullary":
                if self.action == "lower":
                    return token.lower()
                if self.action == "upper":
                    return token.upper()
                if self.action == "degenerate":
                    return self.degenerate(token)
            
            elif self.arity == "nary":
                if self.action == "substitute":
                    result = self.value[0][0].sub(self.value[0][1], token)
                    for pattern, replacement in self.value[1:]:
                        result = pattern.sub(replacement, result)
                    return result
        
        ev = evaluate()
        if len(ev) == 0:
            ev = '""'
        return unicode(ev)
    
    def degenerate(self, s):
        assert (s != "")
        
        result = s[0]
        for c in s[1:]:
            if c != result[-1]:
                result += c
        return result


class BooleanNode(Node):
    """
    BooleanNode allows to write boolean expressions in XML.
    The syntax is a little bit "heavy", but allows simpler parsing and control.
    
    example:
    Checking whether the current token starts with an
    uppercase and is not at the beginning of the sentence.
    (BOS: Beginning Of Sentence)
    
    <expression name="upperNotBeginning">
        <and>
            <left>
                <unary action="isUpper">0</unary>
            </left>
            <right>
                <not>
                    <nullary action="BOS" />
                </not>
            </right>
        </and>
    </expression>
    
    Or, in a more "programmatic" way:
        isUpper(current_token[0]) and not(BOS(current_token))
    Forcing left and right allows to have at most two sons, which allows
    a better control over what the end-user can do and make the parsing
    by far easier.
    The only con is that it may lead to bloated expressions in some cases.
    
    TODO: make a separate class for the Nary nodes..? Currently, a Nary
    node can be the root of an expression. Nary nodes may only be returning
    boolean values in an Expression Node. However, we may want to make
    some subsitution that could be delt with using an Nary node.
    """
    
    def __init__(self, column):
        super(BooleanNode, self).__init__(column)
        self.left  = None
        self.right = None
    
    def parse(self, elt, parent):
        if elt == []:
            return
        else:
            current     = elt.getchildren()
            self.parent = parent
            if len(current) == 0: # value
                self.shift = Node.get_shift(self.value)
                return
            if len(current) == 1: # operand or value
                if current[0].tag in ["and", "or", "not"]:
                    self.value = current[0].tag
                else:
                    self.value = current[0]
                if current[0].tag == "not":
                    self.left = BooleanNode(self.entry)
                    self.left.parse(current[0], self)
                else:
                    self.parse(current[0], self)
            elif len(current) == 2: # (values) or (operand and value)
                self.left  = BooleanNode(self.entry)
                self.right = BooleanNode(self.entry)
                
                self.left.parse(current[0], self)
                self.right.parse(current[1], self)
                
                if current[0] == []: # value
                    self.left.shift = Node.get_shift(self.left.value)
                    self.left.entry = self.get_entry(self.value)
                if current[1] == []: # value
                    self.shift = Node.get_shift(self.right.value)
                    self.entry = self.get_entry(self.value)
            else:
                raise RuntimeError("Could not parse.")
    
    def eval(self, sentdict, position):
        def evaluate(self):
            if self.value == "and":
                if self.left and self.right:
                    return evaluate(self.left) and evaluate(self.right)
                else:
                    raise ValueError("Cannot evaluate and expression : at least one child missing for AND operation.")
            elif self.value == "or":
                if self.left and self.right:
                    return evaluate(self.left) or evaluate(self.right)
                else:
                    raise ValueError("Cannot evaluate or expression : at least one child missing for OR operation.")
            elif self.value == "not":
                if self.left:
                    return not(evaluate(self.left))
                else:
                    raise ValueError("Cannot evaluate or expression : no left child for NOT operation.")
            else:
                arity = self.value.tag
                index = position + self.shift
                
                if index < 0 or index >= len(sentdict):
                    return False
                if arity == "nullary":
                    return self.nullary(sentdict, index)
                if arity == "unary":
                    return self.unary(sentdict, index)
        return evaluate(self)
    
    def nullary(self, sentdict, position):
        action = self.value.attrib["action"].lower()
        entry  = self.entry
        
        if action == "isupper":
            return sentdict[position][entry].isupper()
        elif action == "bos": # beginning of sentence
            return position == 0
        elif action == "eos": # end of...
            return position == len(sentdict) - 1
        elif action == "mos": # middle of...
            if len(sentdict) % 2 == 0:
                mid = len(sentdict) / 2
                return (position == mid) or (position == mid - 1)
            else:
                return position == len(sentdict) / 2
        else:
            raise RuntimeError("Unknown nullary operation: " + action)
    
    def unary(self, sentdict, position):
        action = self.value.attrib["action"].lower()
        entry  = self.entry
        val    = self.value.text
        
        if action == "isupper":
            return sentdict[position][entry][int(val)].isupper()
        if action == "equals":
            return sentdict[position][entry] == val
        if action == "regexp":
            regexp = re.compile(val, re.MULTILINE)
            return regexp.search(sentdict[position][entry]) is not None
        else:
            raise RuntimeError("Unknown unary operation: " + action)


class ListNode(Node):
    """
    ListNode allows to have refined control over a list of checks.
    Those checks are either a string equality or regexp matching.
    You can have different cardinalities:
        - none: not a single element must be checked
        - one : exactly one element must be checked
        - some: at least one element must be checked
        - all : every element must be checked
    """
    
    @classmethod
    def equals_s(cls, left, token):
        return left == token
    
    @classmethod
    def equals_i(cls, left, token):
        return left.lower() == token.lower()
    
    @classmethod
    def check_regexp(cls, regexp, token):
        return regexp.search(token) is not None
    
    @classmethod
    def none(cls, elements, token):
        for e in self.elements:
            if element["check"](element["text"], token):
                return False
        return True
    
    @classmethod
    def one(cls, elements, token):
        i = 0
        for element in self.elements:
            i += int(element["check"](element["text"], token))
            if i > 1:
                break
        return 1 == i
    
    @classmethod
    def some(cls, elements, token):
        result = False
        for element in elements:
            result = element["check"](element["text"], token)
            if result:
                break
        return result
    
    @classmethod
    def all(cls, elements, token):
        for element in self.elements:
            if not element["check"](element["text"], token):
                return False
        return True
    
    def __init__(self, column):
        super(ListNode, self).__init__(column)
        self.elements = None
    
    def parse(self, elt, parent):
        self.parent   = None
        self.value    = elt.attrib["action"]
        self.elements = elt.getchildren()
        self.shift    = Node.get_shift(elt)
        self.entry    = self.get_entry(elt)
        
        if self.value not in ["none", "one", "some", "all"]: raise ValueError('Invalid value in "%s" for action field: %s' %(elt.attrib["name"], self.value))
        
        for i in range(len(self.elements)):
            element = self.elements[i]
            elttype = element.attrib["type"].lower() if "type" in element.attrib else "string"
            casing  = element.attrib["casing"].lower() if "casing" in element.attrib else 's'
            
            if "string" == elttype:
                self.elements[i] = {"text": element.text}
                if 's' == casing:
                    self.elements[i]["check"] = equals_s
                elif 'i' == casing:
                    self.elements[i]["check"] = equals_i
            elif "regexp" == elttype:
                self.elements[i]          = {"text": re.compile(element.text, re.MULTILINE + re.UNICODE + (re.IGNORECASE if 'i' == casing else 0))}
                self.elements[i]["check"] = ListNode.check_regexp
        
        if "none" == self.value:
            self.evaluate = ListNode.none
        elif "one" == self.value:
            self.evaluate = ListNode.one
        elif "some" == self.value:
            self.evaluate = ListNode.some
        elif "all" == self.value:
            self.evaluate = ListNode.all
        else:
            raise ValueError('In "%s": unexpected value "%s"' %(elt.attrib["name"], self.value))
    
    def eval(self, sentdict, position):
        index = position + self.shift
        entry = self.entry
        if index < 0 or index >= len(sentdict):
            return False
        
        word = sentdict[index][entry]
        
        return self.evaluate(self.elements, word)


class RegexpNode(Node):
    """
    RegexpNode allows to use regular expressions in various ways.
    At the current time, it allows to extract three "kinds" of informations:
        - check      : returns whether or not the expression is matched
        - subsequence: returns the matching subsequence if any, otherwise "_no-match_"
        - token      : returns the token is a match is found, otherwise "_no-match_"
    """
    
    @classmethod
    def check(cls, regexp, token):
        return regexp.search(token) is not None
    
    @classmethod
    def subsequence(cls, regexp, token):
        matching = regexp.search(token)
        if matching is not None:
            return matching.group()
        else:
            return "_no-match_"
    
    @classmethod
    def token(cls, regexp, token):
        if regexp.search(token) is not None:
            return token
        else:
            return "_no-match_"
    
    def __init__(self, column):
        super(RegexpNode, self).__init__(column)
        self.pattern = None
    
    def parse(self, elt, parent):
        self.parent  = None
        self.value   = elt.attrib["action"].lower()
        self.pattern = elt.getchildren()[0]
        self.shift   = Node.get_shift(elt.getchildren()[0])
        self.entry   = self.get_entry(elt.getchildren()[0])
        self.flags   = re.MULTILINE
        self.regexp  = None
        self.matcher = None
        
        if self.pattern.tag != "pattern": raise ValueError('Invalid XML tag inside regexp node: ' + self.pattern.tag)
        if "check" == self.value:
            self.matcher = RegexpNode.check
        elif "subsequence" == self.value:
            self.matcher = RegexpNode.subsequence
        elif "token" == self.value:
            self.matcher = RegexpNode.token
        else:
            raise ValueError('In "%s": invalid value for value field: %s' %(elt.attrib["name"], self.value))
        
        casing = self.pattern.attrib["casing"].lower() if "casing" in self.pattern.attrib else 's'
        if casing not in "is": raise ValueError('Invalid value for casing field: ' + casing)
        if casing == 's':
            None
        elif casing == 'i':
            self.flags += re.IGNORECASE
        self.regexp = re.compile(self.pattern.text, self.flags)
        
    
    def eval(self, sentdict, position):
        index = position + self.shift
        entry = self.entry
        if index < 0 or index >= len(sentdict):
            return "_no-match_"
        
        word   = sentdict[index][entry]
        return self.matcher(self.regexp, word)

"""
class SequenceNode(Node):
    def __init__(self, column):
        super(RegexpNode, self).__init__(column)
    
    def parse(self, elt, parent):
        self.parent = None
        self.value  = elt.getchildren()
    
    def apply(self, sentdict):
        def check(entry_type, text, token):
            if entry_type == "string":
                return token == text
            elif entry_type == "regexp":
                return re.compile(text, re.M + re.U).search(token) is not None
        
        def eval_item(item, start):
            cardinality = item.attrib["card"] if "card" in item.attrib else ""
            entry_type  = self.get_entry(item)
            current     = start
            if cardinality == "":
                checked = check(entry_type, item.text, start)
            elif cardinality == "?":
            elif cardinality == "*":
            elif cardinality == "+":
        position = 0
        current  = 0
        
        current_value = self.value[0]
        entry         = self.get_entry(current_value)
        regexp        = re.compile(current_value.text, re.U + re.M)
        cardinality   = ("" if "cardinality" not in current_value.attrib else current_value.attrib["cardinality"])
        while position < len(sentdict):
            if 
            
            position += 1
    
    def eval(self, sentdict, position):
        raise RuntimeError("eval undefined for type MultiWordNode.")"""
    
    
class ConditionalNode(Node):
    """
    ConditionalNode allows to extract information only under given circumstances.
    A trigger must first be given, then the information to be extracted. It can
    be anything supported by the language.
    The trigger returns, obviously, a boolean. If the trigger returns False, the
    eval method returns "_untriggered_"
    """
    
    def __init__(self, column):
        super(ConditionalNode, self).__init__(column)
        self.trigger = None
    
    def parse(self, elt, parent):
        children = elt.getchildren()
        if len(children) != 2: raise ValueError('Conditional Node "%s" does not have exactly 2 children: %i' %(elt.attrib["name"], len(children)))
        
        self.parent    = None
        trigger, value = children
        
        if trigger.tag != "trigger": raise ValueError('Invalid value for trigger field: ' + self.trigger.tag)
        self.trigger = NodeFromName(trigger.getchildren()[0].tag)
        self.trigger.parse(trigger.getchildren()[0], self)
        
        # here we are to check whether the trigger has a boolean return value
        if not returns_boolean(self.trigger):
            raise ValueError('Non boolean value for trigger node "%s": "%s"' %(elt.attrib["name"], self.trigger.value))
        
        # There is supposedly nothing to check here
        self.value = NodeFromName(value.tag)
        self.value.parse(value, self)
    
    def eval(self, sentdict, position):
        triggered = Node.str_to_boolean(self.trigger.eval(sentdict, position))
        
        if triggered:
            return self.value.eval(sentdict, position)
        else:
            return "_untriggered_"


class TokenNode(Node):
    """
    TokenNode allows to check whether a token is in a dictionary that is a set
    of values.
    """
    
    def __init__(self, column, path):
        super(TokenNode, self).__init__(column)
        self.path = path # path to the configuration file
    
    def parse(self, elt, parent):
        self.parent = None
        self.path   = join(dirname(abspath(self.path)), elt.attrib["path"]) # path of the file relatively to the directory containing the configuration file
        self.value  = cPickle.load(open(self.path))
        self.shift  = Node.get_shift(elt)
        self.entry  = self.get_entry(elt)
        
        self.casing = "normal"
        if "casing" in elt.attrib:
            if "casing" in ("normal", "lower", "upper"): # normal: no modification. lower: tokens are in lower case. upper: tokens are in upper case.
                self.casing = elt.attrib["casing"]
            else:
                raise ValueError('Invalid casing for token node "%s": "%s"' %(elt.attrib["name"], self.casing))
        
    
    def eval(self, sentdict, position):
        def evaluate():
            index = position + self.shift
            entry = self.entry
            if index < 0 or index >= len(sentdict):
                return "_null_"
            
            word = sentdict[index][entry]
            
            if self.casing == "normal":
                None
            elif self.casing == "lower":
                word = word.lower()
            elif self.casing == "upper":
                word = word.upper()
            else:
                raise ValueError('Invalid casing for token node "%s": "%s"' %(elt.attrib["name"], self.casing))
            
            return word in self.value
        
        return unicode(evaluate())


class MultiWordNode(Node):
    """
    MultiWordNode allows to check whether sequences of tokens are in a dictionary.
    """
    
    def __init__(self, column, path):
        super(MultiWordNode, self).__init__(column)
        self.path      = path # path to the configuration file
        self.appendice = ""
        self.casing    = "normal"
    
    def parse(self, elt, parent):
        self.parent = None
        self.path   = join(dirname(abspath(self.path)), elt.attrib["path"]) # path of the file relatively to the directory containing the configuration file
        self.value  = cPickle.load(open(self.path))
        self.entry  = self.get_entry(elt)
        
        if "appendice" in elt.attrib:
            self.appendice = elt.attrib["appendice"]
        if "casing" in elt.attrib:
            if "casing" in ("normal", "lower", "upper"): # normal: no modification. lower: tokens are in lower case. upper: tokens are in upper case.
                self.casing = elt.attrib["casing"]
            else:
                raise ValueError('Invalid casing for multiword node "%s": "%s"' %(elt.attrib["name"], self.casing))
            
        
    def eval(self, sentdict, position):
        raise RuntimeError("eval undefined for type MultiWordNode.")


def EndogenousNodeFromName(name, column):
    if name == "expression":
        return BooleanNode(column)
    elif name == "list":
        return ListNode(column)
    elif name == "regexp":
        return RegexpNode(column)
    elif name == "conditional":
        return ConditionalNode(column)
    elif name.endswith("ary"):
        return NaryNode(column)
    else:
        raise ValueError("Unknown name: " + name)


def ExogenousNodeFromName(name, column, path):
    if name == "token":
        return TokenNode(column, path)
    elif name == "multiword":
        return MultiWordNode(column, path)
    else:
        raise ValueError("Unknown name: " + name)


class Tree(object):
    def __init__(self, root):
        self.root  = root
        self._name = None
    
    def get_name(self):
        return self._name
    
    def parse(self, elt):
        self.root.parse(elt, None)
        self._name = elt.attrib["name"]
    
    def eval(self, sentdict, position):
        return self.root.eval(sentdict, position)
