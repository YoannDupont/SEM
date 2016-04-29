#-------------------------------------------------------------------------------
#
# file: __init__.py
#
# Description: an __init__ file to allow the use of python sources as modules
#
# author: Yoann Dupont
# copyright (c) 2016 Yoann Dupont - all rights reserved
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#-------------------------------------------------------------------------------


#------------------#
# "constant" masks #
#------------------#
MASKS = [2**i for i in range(0, 31)]
POS = MASKS[0]
CHUNK = MASKS[1]


# returns the mask value of the string in parameter
def val(string):
    string = string.upper()

    if string == "POS":
        return POS
    elif string == "CHUNK":
        return CHUNK
    else:
        raise ValueError(u"Invalid code : " + string)

# code is a string containing the different codes representing the wanted
# labellings. POS, CHUNK, POS+CHUNK are examples of such codes.
def getcode(code):
    if code is None:
        raise ValueError(u"No code given in parameter !")
    else:
        codelist = list(set([s.upper() for s in code.split("+")]))
        code = sum([val(c) for c in codelist])
        del codelist[:]
        return code
