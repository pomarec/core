import grp
import ldap
import ldap.modlist

from arkos import conns
from arkos.utilities import shell


class Group:
    def __init__(self, name="", gid=0, users=[], rootdn="dc=arkos-servers,dc=org"):
        self.name = name
        self.gid = gid or get_next_gid()
        self.users = users
        self.rootdn = rootdn
    
    def add(self):
        try:
            ldif = conns.LDAP.search_s("cn=%s,ou=groups,%s" % (self.name,self.rootdn),
                ldap.SCOPE_SUBLIST, "(objectClass=*)", None)
            raise Exception("A group with this name already exists")
        except ldap.NO_SUCH_OBJECT:
            pass
        ldif = {
            "objectClass": ["posixGroup", "top"],
            "cn": self.name,
            "gidNumber": str(self.gid),
            "memberUid": users
        }
        ldif = ldap.modlist.addModlist(ldif)
        conns.LDAP.add_s("cn=%s,ou=groups,%s" % (self.name,self.rootdn), ldif)
    
    def update(self):
        try:
            ldif = conns.LDAP.search_s("cn=%s,ou=groups,%s" % (self.name,self.rootdn),
                ldap.SCOPE_SUBLIST, "(objectClass=*)", None)
        except ldap.NO_SUCH_OBJECT:
            raise Exception("This group does not exist")

        ldif = ldif[0][1]
        attrs = {"memberUid": self.users}
        nldif = ldap.modlist.modifyModlist(ldif, attrs, ignore_oldexistent=1)
        conns.LDAP.modify_ext_s("cn=%s,ou=groups,%s" % (self.name,self.rootdn), nldif)
    
    def delete(self):
        conns.LDAP.delete_s("cn=%s,ou=groups,%s" % (self.name,self.rootdn))


class SystemGroup:    
    def __init__(self, name="", gid=0, users=[]):
        self.name = name
        self.gid = gid
        self.users = users

    def add(self):
        shell("groupadd %s" % self.name)
        self.update()
        for x in grp.getgrall():
            if x.gr_name == self.name:
                self.gid = x.gr_gid
    
    def update(self):
        for x in self.users:
            shell("usermod -a -G %s %s" % (self.name, x))

    def delete(self):
        shell("groupdel %s" % self.name)


def get(gid=None):
    r = []
    for x in conns.LDAP.search_s("ou=groups,%s" % self.rootdn, ldap.SCOPE_SUBTREE,
         "(objectClass=*)", None):
        g = Group(name=x[1]["cn"], gid=x[1]["gidNumber"], users=x[1]["memberUid"],
            rootdn=x[0].split("ou=users,")[1])
        if g.name == gid:
            return g
        r.append(g)
    return r if not gid else None

def get_system(gid=None):
    r = []
    for x in grp.getgrall():
        g = SystemGroup(name=x.gr_name, gid=x.gr_gid, users=x.gr_mem)
        if gid == g.name:
            return g
        r.append(g)
    return r if not gid else None

def get_next_gid(self):
    return max([x.gid for x in get_system()]) + 1
