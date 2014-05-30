import re, cPickle, os.path

join    = os.path.join
abspath = os.path.abspath
dirname = os.path.dirname
    
class Node(object):
    def __init__(self):
        self.parent = None
        self.value  = None
        self.shift  = None
    
    @staticmethod
    def get_shift(node):
        return int(node.attrib["x"]) if "x" in node.attrib else 0
    
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
    
    def __init__(self):
        super(BooleanNode, self).__init__()
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
                    self.left = BooleanNode()
                    self.left.parse(current[0], self)
                else:
                    self.parse(current[0], self)
            elif len(current) == 2: # (values) or (operand and value)
                self.left  = BooleanNode()
                self.right = BooleanNode()
                
                self.left.parse(current[0], self)
                self.right.parse(current[1], self)
                
                if current[0] == []: # value
                    self.left.shift = Node.get_shift(self.left.value)
                if current[1] == []: # value
                    self.shift = Node.get_shift(self.right.value)
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
                arity  = self.value.tag
                index = position + self.shift
                
                if index < 0 or index >= len(sentdict):
                    return False
                if arity == "nullary":
                    return self.nullary(sentdict, index)
                if arity == "unary":
                    return self.unary(sentdict, index)
        return unicode(evaluate(self))
    
    def nullary(self, sentdict, position):
        action = self.value.attrib["action"].lower()
        
        if action == "isupper":
            return sentdict[position]['word'].isupper()
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
        val    = self.value.text
        
        if action == "isupper":
            return sentdict[position]['word'][int(val)].isupper()
        if action == "equals":
            return sentdict[position]['word'] == val
        if action == "regexp":
            regexp = re.compile(val, re.MULTILINE)
            return regexp.search(sentdict[position]['word']) is not None
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
    
    def __init__(self):
        super(ListNode, self).__init__()
        self.elements = None
    
    def parse(self, elt, parent):
        self.parent   = None
        self.value    = elt.attrib["action"]
        self.elements = elt.getchildren()
        
        if self.value not in ["none", "one", "some", "all"]: raise ValueError('Invalid value in "%s" for action field: %s' %(elt.attrib["name"], self.value))
    
    def eval(self, sentdict, position):
        def evaluate(element):
            index = position + Node.get_shift(e)
            if index < 0 or index >= len(sentdict):
                return False
            
            casing = element.attrib["casing"].lower() if "casing" in element.attrib else 's'
            if casing not in "is": raise ValueError('Invalid value for casing field: ' + casing)
            
            mt   = element.attrib["type"].lower() if "type" in element.attrib else "string" # matching type
            word = sentdict[index]["word"]
            if mt == "string":
                if casing == 's':
                    return word == element.text
                elif casing == 'i':
                    return word.lower() == element.text.lower()
            elif mt == "regexp":
                flags = re.MULTILINE
                if casing == 's':
                    None
                elif casing == 'i':
                    flags += re.IGNORECASE
                
                regexp = re.compile(element.text, flags)
                return regexp.search(word) is not None
        
        value  = self.value.lower()
        result = None
        if value == "none":
            result = True
            for e in self.elements:
                if evaluate(e):
                    result = False
                    break
        elif value == "one":
            i = 0
            for e in self.elements:
                i += (1 if evaluate(e) else 0)
                if i > 1:
                    result = True
                    break
            result = i == 1
        elif value == "some":
            result = False
            for e in self.elements:
                result = evaluate(e)
                if result:
                    break
        elif value == "all":
            result = True
            for e in self.elements:
                if not evaluate(e):
                    result = False
                    break
        return unicode(result)


class RegexpNode(Node):
    """
    RegexpNode allows to use regular expressions in various ways.
    At the current time, it allows to extract three "kinds" of informations:
        - check      : returns whether or not the expression is matched
        - subsequence: returns the matching subsequence if any, otherwise "_no-match_"
        - token      : returns the token is a match is foudn, otherwise "_no-match_"
    """
    
    def __init__(self):
        super(RegexpNode, self).__init__()
        self.pattern = None
    
    def parse(self, elt, parent):
        self.parent  = None
        self.value   = elt.attrib["action"]
        self.pattern = elt.getchildren()[0]
        self.shift   = Node.get_shift(elt.getchildren()[0])
        
        if self.value not in set(["check", "subsequence", "token"]): raise ValueError('Invalid value for value field: ' + self.value)
        if self.pattern.tag != "pattern": raise ValueError('Invalid XML tag inside regexp node: ' + self.pattern.tag)
        
    
    def eval(self, sentdict, position):
        def evaluate():
            index = position + self.shift
            if index < 0 or index >= len(sentdict):
                return "_no-match_"
        
            casing = self.pattern.attrib["casing"].lower() if "casing" in self.pattern.attrib else 's'
            if casing not in "is": raise ValueError('Invalid value for casing field: ' + casing)
            
            flags = re.MULTILINE
            if casing == 's':
                None
            elif casing == 'i':
                flags += re.IGNORECASE
            
            regexp = re.compile(self.pattern.text, flags)
            value = self.value
            word  = sentdict[index]["word"]
            if value == "check":
                return regexp.search(word) is not None
            elif value == "subsequence":
                matching = regexp.search(word)
                if matching is not None:
                    return matching.group()
                else:
                    return "_no-match_"
            elif value == "token":
                if regexp.search(word) is not None:
                    return word
                else:
                    return "_no-match_"
        
        return unicode(evaluate())
    
    
class ConditionalNode(Node):
    """
    ConditionalNode allows to extract information only under given circumstances.
    A trigger must first be given, then the information to be extracted. It can
    be anything supported by the language.
    The trigger returns, abviously, a boolean. If the trigger returns False, the
    eval method returns "_untriggered_"
    """
    
    def __init__(self):
        super(ConditionalNode, self).__init__()
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
            raise ValueError('"Non boolean value for trigger node "%s": "%s"' %(elt.attrib["name"], self.trigger.value))
        """if isinstance(self.trigger, RegexpNode):
            if self.trigger.value != "check":
                raise ValueError('"Non boolean value for trigger node "%s": "%s"' %(elt.attrib["name"], self.trigger.value))"""
        
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
    
    def __init__(self, path):
        super(TokenNode, self).__init__()
        self.path = path # path to the configuration file
    
    def parse(self, elt, parent):
        self.parent = None
        self.path   = join(dirname(abspath(self.path)), elt.attrib["path"]) # path of the file relatively to the directory containing the configuration file
        
        self.value = cPickle.load(open(self.path))
        self.shift = Node.get_shift(elt)
        
    
    def eval(self, sentdict, position):
        def evaluate():
            index = position + self.shift
            if index < 0 or index >= len(sentdict):
                return "_null_"
            
            word = sentdict[index]["word"]
            
            return word in self.value
        
        return unicode(evaluate())


class MultiWordNode(Node):
    """
    MultiWordNode allows to check whether sequences of tokens are in a dictionary.
    """
    
    def __init__(self, path):
        super(TokenNode, self).__init__()
        self.path = path # path to the configuration file
    
    def parse(self, elt, parent):
        self.parent = None
        self.path   = join(dirname(abspath(self.path)), elt.attrib["path"]) # path of the file relatively to the directory containing the configuration file
        
        self.value = cPickle.load(open(self.path))
        
    def eval(self, sentdict, position):
        raise RuntimeError("eval undefined for type MultiWordNode.")


def EndogeneNodeFromName(name):
    if name == "expression":
        return BooleanNode()
    elif name == "list":
        return ListNode()
    elif name == "regexp":
        return RegexpNode()
    elif name == "conditional":
        return ConditionalNode()
    else:
        raise ValueError("Unknown name: " + name)


def ExogeneNodeFromName(name, path):
    if name == "token":
        return TokenNode(path)
    elif name == "multiword":
        return MultiWordNode(path)
    else:
        raise ValueError("Unknown name: " + name)


class Tree(object):
    def __init__(self, root):
        self.root = root
        self._name = None
    
    def get_name(self):
        return self._name
    
    def parse(self, elt):
        self.root.parse(elt, None)
        self._name = elt.attrib["name"]
    
    def eval(self, sentdict, position):
        return self.root.eval(sentdict, position)
