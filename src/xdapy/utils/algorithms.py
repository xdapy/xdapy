"""A collection of general algorithms

Created on Jul 30, 2009
    levenshtein
   
"""
# alphabetical order by last name, please
import copy, uuid, hashlib

__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>',
               '"Rike-Benjamin Schuppner <rikebs@debilski.de>"']

def levenshtein(s1, s2):
    """Find the Levenshtein distance between two strings.
     
    http://en.wikibooks.org/wiki/Algorithm_implementation/Strings/Levenshtein_distance
    (Note that while compact, the runtime of this implementation is relatively poor.) 
    
    """
    
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if not s1:
        return len(s2)
 
    previous_row = xrange(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
 
    return previous_row[-1]

def lev(a, b):
    if not a: return len(b)
    if not b: return len(a)
    return min(lev(a[1:], b[1:]) + (a[0] != b[0]), lev(a[1:], b) + 1, lev(a, b[1:]) + 1)

def listequal(a, b):
    if not isinstance(a, list) or not isinstance(b, list):
        return False
    if len(a) is not len(b):
        return False
    b_c = copy.deepcopy(b)
    for item in a:
        try:
            b_c.remove(item)
        except:
            return False
    if b_c:
        return False
    return True

def gen_uuid():
    return str(uuid.uuid4())

def hash_dict(attrs):
      """Generates a hash from a simple dict containing string keys and values."""
      string = "{"
      ordered = ['"' + k.lower() + '":"' + attrs[k].lower() + '"'
                       for k in sorted(attrs.keys())]
      string = "{" + ",".join(ordered) + "}"

      md5 = hashlib.md5()
      md5.update(string)
      the_hash = md5.hexdigest()
      return the_hash

def filter_none(a_dict):
    """Filters all elements from the dict with value is None."""
    return dict((k, v) for k, v in a_dict if v)



