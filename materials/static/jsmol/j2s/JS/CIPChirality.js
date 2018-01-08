Clazz.declarePackage ("JS");
Clazz.load (["JU.BS", "$.Lst", "$.V3"], "JS.CIPChirality", ["java.util.Arrays", "$.Hashtable", "JU.Measure", "$.P4", "$.PT", "JU.BSUtil", "$.Elements", "$.Logger", "JV.JC"], function () {
c$ = Clazz.decorateAsClass (function () {
this.isRule4TEST = false;
this.ptID = 0;
this.root = null;
this.currentRule = 1;
this.lstSmallRings = null;
this.bsAtropisomeric = null;
this.bsKekuleAmbiguous = null;
this.bsAzacyclic = null;
this.vNorm = null;
this.vNorm2 = null;
this.vTemp = null;
this.rule1bOption = 1;
this.setAuxiliary = false;
this.rootRule = 0;
if (!Clazz.isClassDefined ("JS.CIPChirality.CIPAtom")) {
JS.CIPChirality.$CIPChirality$CIPAtom$ ();
}
Clazz.instantialize (this, arguments);
}, JS, "CIPChirality");
Clazz.prepareFields (c$, function () {
this.lstSmallRings =  new JU.Lst ();
this.vNorm =  new JU.V3 ();
this.vNorm2 =  new JU.V3 ();
this.vTemp =  new JU.V3 ();
});
Clazz.defineMethod (c$, "getRuleName", 
function (rule) {
if (rule == 99) return "RS";
return JS.CIPChirality.ruleNames[rule];
}, "~N");
Clazz.makeConstructor (c$, 
function () {
});
Clazz.defineMethod (c$, "init", 
 function () {
this.ptID = 0;
this.lstSmallRings.clear ();
this.bsKekuleAmbiguous = null;
this.bsAtropisomeric =  new JU.BS ();
});
Clazz.defineMethod (c$, "getChiralityForAtoms", 
function (atoms, bsAtoms, bsAtropisomeric, bsHelixM, bsHelixP, setAuxiliary) {
if (bsAtoms.isEmpty ()) return;
this.init ();
this.setAuxiliary = (setAuxiliary && bsAtoms.cardinality () == 1);
this.bsAtropisomeric = (bsAtropisomeric == null ?  new JU.BS () : bsAtropisomeric);
var bs = JU.BSUtil.copy (bsAtoms);
this.lstSmallRings =  new JU.Lst ();
while (!bs.isEmpty ()) this.getSmallRings (atoms[bs.nextSetBit (0)], bs);

this.bsKekuleAmbiguous = this.getKekule (atoms);
this.bsAzacyclic = this.getAzacyclic (atoms, bsAtoms);
var bsToDo = JU.BSUtil.copy (bsAtoms);
var haveAlkenes = this.preFilterAtomList (atoms, bsToDo);
for (var i = bsToDo.nextSetBit (0); i >= 0; i = bsToDo.nextSetBit (i + 1)) {
var a = atoms[i];
a.setCIPChirality (0);
this.ptID = 0;
var c = this.getAtomChiralityLimited (a, null, null);
a.setCIPChirality (c == 0 ? 3 : c | ((this.currentRule - 1) << 5));
}
if (haveAlkenes) {
var lstEZ =  new JU.Lst ();
for (var i = bsToDo.nextSetBit (0); i >= 0; i = bsToDo.nextSetBit (i + 1)) this.getAtomBondChirality (atoms[i], lstEZ, bsToDo);

if (this.lstSmallRings.size () > 0 && lstEZ.size () > 0) this.clearSmallRingEZ (atoms, lstEZ);
if (bsHelixM != null) for (var i = bsHelixM.nextSetBit (0); i >= 0; i = bsHelixM.nextSetBit (i + 1)) atoms[i].setCIPChirality (17);

if (bsHelixP != null) for (var i = bsHelixP.nextSetBit (0); i >= 0; i = bsHelixP.nextSetBit (i + 1)) atoms[i].setCIPChirality (18);

}if (JU.Logger.debugging) {
JU.Logger.info ("sp2-aromatic = " + this.bsKekuleAmbiguous);
JU.Logger.info ("smallRings = " + JU.PT.toJSON (null, this.lstSmallRings));
}}, "~A,JU.BS,JU.BS,JU.BS,JU.BS,~B");
Clazz.defineMethod (c$, "getAzacyclic", 
 function (atoms, bsAtoms) {
var bsAza = null;
for (var i = bsAtoms.nextSetBit (0); i >= 0; i = bsAtoms.nextSetBit (i + 1)) {
var atom = atoms[i];
if (atom.getElementNumber () != 7 || atom.getCovalentBondCount () != 3 || this.bsKekuleAmbiguous.get (i)) continue;
var nRings =  new JU.Lst ();
for (var j = this.lstSmallRings.size (); --j >= 0; ) {
var bsRing = this.lstSmallRings.get (j);
if (bsRing.get (i)) nRings.addLast (bsRing);
}
var nr = nRings.size ();
if (nr < 2) continue;
var bsSubs =  new JU.BS ();
var bonds = atom.getEdges ();
for (var b = bonds.length; --b >= 0; ) if (bonds[b].isCovalent ()) bsSubs.set (bonds[b].getOtherNode (atom).getIndex ());

var bsBoth =  new JU.BS ();
var bsAll =  new JU.BS ();
for (var j = 0; j < nr - 1 && bsAll != null; j++) {
var bs1 = nRings.get (j);
for (var k = j + 1; k < nr && bsAll != null; k++) {
var bs2 = nRings.get (k);
JU.BSUtil.copy2 (bs1, bsBoth);
bsBoth.and (bs2);
if (bsBoth.cardinality () > 2) {
JU.BSUtil.copy2 (bs1, bsAll);
bsAll.or (bs2);
bsAll.and (bsSubs);
if (bsAll.cardinality () == 3) {
if (bsAza == null) bsAza =  new JU.BS ();
bsAza.set (i);
bsAll = null;
}}}
}
}
return bsAza;
}, "~A,JU.BS");
Clazz.defineMethod (c$, "preFilterAtomList", 
 function (atoms, bsToDo) {
var haveAlkenes = false;
for (var i = bsToDo.nextSetBit (0); i >= 0; i = bsToDo.nextSetBit (i + 1)) {
if (!this.couldBeChiralAtom (atoms[i])) {
bsToDo.clear (i);
continue;
}if (!haveAlkenes && this.couldBeChiralAlkene (atoms[i], null) != -1) haveAlkenes = true;
}
return haveAlkenes;
}, "~A,JU.BS");
Clazz.defineMethod (c$, "couldBeChiralAtom", 
 function (a) {
var mustBePlanar = false;
switch (a.getCovalentBondCount ()) {
default:
System.out.println ("?? too many bonds! " + a);
return false;
case 0:
return false;
case 1:
return false;
case 2:
return a.getElementNumber () == 7;
case 3:
switch (a.getElementNumber ()) {
case 7:
if (this.bsAzacyclic != null && this.bsAzacyclic.get (a.getIndex ())) break;
return false;
case 6:
mustBePlanar = true;
break;
case 15:
case 16:
case 33:
case 34:
case 51:
case 52:
case 83:
case 84:
break;
case 4:
break;
default:
return false;
}
break;
case 4:
break;
}
var edges = a.getEdges ();
var nH = 0;
var haveDouble = false;
for (var j = edges.length; --j >= 0; ) {
if (mustBePlanar && edges[j].getCovalentOrder () == 2) haveDouble = true;
if (edges[j].getOtherNode (a).getIsotopeNumber () == 1) nH++;
}
return (nH < 2 && (haveDouble || mustBePlanar == Math.abs (this.getTrigonality (a, this.vNorm)) < 0.2));
}, "JU.SimpleNode");
Clazz.defineMethod (c$, "couldBeChiralAlkene", 
 function (a, b) {
switch (a.getCovalentBondCount ()) {
default:
return -1;
case 2:
if (a.getElementNumber () != 7) return -1;
break;
case 3:
if (!this.isFirstRow (a)) return -1;
break;
}
var bonds = a.getEdges ();
var n = 0;
for (var i = bonds.length; --i >= 0; ) if (bonds[i].getCovalentOrder () == 2) {
if (++n > 1) return 17;
var other = bonds[i].getOtherNode (a);
if (!this.isFirstRow (other)) return -1;
if (b != null && (other !== b || b.getCovalentBondCount () == 1)) {
return -1;
}}
return 5;
}, "JU.SimpleNode,JU.SimpleNode");
Clazz.defineMethod (c$, "isFirstRow", 
function (a) {
var n = a.getElementNumber ();
return (n > 2 && n <= 10);
}, "JU.SimpleNode");
Clazz.defineMethod (c$, "getKekule", 
 function (atoms) {
var nRings = this.lstSmallRings.size ();
var bs =  new JU.BS ();
var bsDone =  new JU.BS ();
for (var i = nRings; --i >= 0; ) {
if (bsDone.get (i)) continue;
var bsRing = this.lstSmallRings.get (i);
if (bsRing.cardinality () != 6) {
bsDone.set (i);
continue;
}var nPI = 0;
for (var j = bsRing.nextSetBit (0); j >= 0; j = bsRing.nextSetBit (j + 1)) {
var a = atoms[j];
if (bs.get (a.getIndex ())) {
nPI++;
continue;
}var nb = a.getCovalentBondCount ();
if (nb == 3 || nb == 2) {
var bonds = a.getEdges ();
for (var k = bonds.length; --k >= 0; ) {
var b = bonds[k];
if (b.getCovalentOrder () != 2) continue;
if (bsRing.get (b.getOtherNode (a).getIndex ())) {
nPI++;
break;
}}
}}
if (nPI == 6) {
bs.or (bsRing);
bsDone.set (i);
i = nRings;
}}
return bs;
}, "~A");
Clazz.defineMethod (c$, "getSmallRings", 
 function (atom, bs) {
(this.root = Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (atom, null, false, false, false)).addSmallRings (bs);
}, "JU.SimpleNode,JU.BS");
Clazz.defineMethod (c$, "clearSmallRingEZ", 
 function (atoms, lstEZ) {
for (var j = this.lstSmallRings.size (); --j >= 0; ) this.lstSmallRings.get (j).andNot (this.bsAtropisomeric);

for (var i = lstEZ.size (); --i >= 0; ) {
var ab = lstEZ.get (i);
for (var j = this.lstSmallRings.size (); --j >= 0; ) {
var ring = this.lstSmallRings.get (j);
if (ring.get (ab[0]) && ring.get (ab[1])) {
atoms[ab[0]].setCIPChirality (3);
atoms[ab[1]].setCIPChirality (3);
}}
}
}, "~A,JU.Lst");
Clazz.defineMethod (c$, "getTrigonality", 
function (a, vNorm) {
var pts =  new Array (4);
var bonds = a.getEdges ();
for (var n = bonds.length, i = n, pt = 0; --i >= 0 && pt < 4; ) if (bonds[i].isCovalent ()) pts[pt++] = bonds[i].getOtherNode (a).getXYZ ();

var plane = JU.Measure.getPlaneThroughPoints (pts[0], pts[1], pts[2], vNorm, this.vTemp,  new JU.P4 ());
return JU.Measure.distanceToPlane (plane, (pts[3] == null ? a.getXYZ () : pts[3]));
}, "JU.SimpleNode,JU.V3");
Clazz.defineMethod (c$, "getAtomBondChirality", 
 function (atom, lstEZ, bsToDo) {
var index = atom.getIndex ();
var bonds = atom.getEdges ();
var c = 0;
var isAtropic = this.bsAtropisomeric.get (index);
for (var j = bonds.length; --j >= 0; ) {
var bond = bonds[j];
var atom1;
var index1;
if (isAtropic) {
atom1 = bonds[j].getOtherNode (atom);
index1 = atom1.getIndex ();
if (!this.bsAtropisomeric.get (index1)) continue;
c = this.setBondChirality (atom, atom1, atom, atom1, true);
} else if (bond.getCovalentOrder () == 2) {
atom1 = this.getLastCumuleneAtom (bond, atom, null, null);
index1 = atom1.getIndex ();
if (index1 < index) continue;
c = this.getBondChiralityLimited (bond, atom);
} else {
continue;
}if (c != 0) {
if (!isAtropic) lstEZ.addLast ( Clazz.newIntArray (-1, [index, index1]));
bsToDo.clear (index);
bsToDo.clear (index1);
}if (isAtropic) break;
}
}, "JU.SimpleNode,JU.Lst,JU.BS");
Clazz.defineMethod (c$, "getLastCumuleneAtom", 
 function (bond, atom, nSP2, parents) {
var atom2 = bond.getOtherNode (atom);
if (parents != null) {
parents[0] = atom2;
parents[1] = atom;
}if (nSP2 != null) nSP2[0] = 2;
var ppt = 0;
while (true) {
if (atom2.getCovalentBondCount () != 2) return atom2;
var edges = atom2.getEdges ();
for (var i = edges.length; --i >= 0; ) {
var atom3 = (bond = edges[i]).getOtherNode (atom2);
if (atom3 === atom) continue;
if (bond.getCovalentOrder () != 2) return atom2;
if (parents != null) {
if (ppt == 0) {
parents[0] = atom2;
ppt = 1;
}parents[1] = atom2;
}if (nSP2 != null) nSP2[0]++;
atom = atom2;
atom2 = atom3;
break;
}
}
}, "JU.SimpleEdge,JU.SimpleNode,~A,~A");
Clazz.defineMethod (c$, "getAtomChiralityLimited", 
 function (atom, cipAtom, parentAtom) {
var rs = 0;
try {
var isAlkeneEndCheck = (atom == null);
if (isAlkeneEndCheck) {
atom = (this.root = cipAtom).atom;
cipAtom.htPathPoints = (cipAtom.parent = Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (parentAtom, null, true, false, false)).htPathPoints;
} else {
if (!(this.root = cipAtom = Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (atom, null, false, false, false)).isSP3) {
return 0;
}}if (cipAtom.setNode ()) {
for (this.currentRule = 1; this.currentRule <= 9; this.currentRule++) {
this.rootRule = this.currentRule;
if (JU.Logger.debugging) JU.Logger.info ("-Rule " + this.getRuleName (this.currentRule) + " CIPChirality for " + cipAtom + "-----");
switch (this.currentRule) {
case 4:
cipAtom.rootRule4bQueue =  new JU.Lst ();
cipAtom.createAuxiliaryDescriptors (null, null);
break;
case 5:
if (cipAtom.rule4Type == 0) {
this.currentRule = 8;
continue;
}case 6:
case 7:
cipAtom.sortSubstituents (-2147483648);
break;
case 9:
rs = cipAtom.setupRule6 (false);
if (rs == 0) continue;
break;
}
var nPrioritiesPrev = cipAtom.nPriorities;
if (rs == 0 && cipAtom.sortSubstituents (0)) {
if (JU.Logger.debugging && cipAtom.h1Count < 2) {
JU.Logger.info (this.currentRule + ">>>>" + cipAtom);
for (var i = 0; i < cipAtom.bondCount; i++) {
if (cipAtom.atoms[i] != null) JU.Logger.info (cipAtom.atoms[i] + " " + cipAtom.priorities[i]);
}
}if (isAlkeneEndCheck) return (cipAtom.atoms[0].isDuplicate ? 2 : 1);
rs = cipAtom.checkHandedness ();
if (this.currentRule == 8 && (cipAtom.nPriorities != 4 || nPrioritiesPrev != 2)) {
rs |= 8;
}if (JU.Logger.debugging) JU.Logger.info (atom + " " + JV.JC.getCIPChiralityName (rs) + " by Rule " + this.getRuleName (this.currentRule) + "\n----------------------------------");
return rs;
}}
}} catch (e) {
System.out.println (e + " in CIPChirality " + this.currentRule);
{
alert(e);
}return 3;
}
return rs;
}, "JU.SimpleNode,JS.CIPChirality.CIPAtom,JU.SimpleNode");
Clazz.defineMethod (c$, "getBondChiralityLimited", 
 function (bond, a) {
if (JU.Logger.debugging) JU.Logger.info ("get Bond Chirality " + bond);
if (a == null) a = bond.getOtherNode (null);
if (this.couldBeChiralAlkene (a, bond.getOtherNode (a)) == -1) return 0;
var nSP2 =  Clazz.newIntArray (1, 0);
var parents =  new Array (2);
var b = this.getLastCumuleneAtom (bond, a, nSP2, parents);
var isAxial = nSP2[0] % 2 == 1;
return this.setBondChirality (a, parents[0], parents[1], b, isAxial);
}, "JU.SimpleEdge,JU.SimpleNode");
Clazz.defineMethod (c$, "setBondChirality", 
 function (a, pa, pb, b, isAxial) {
var a1 = Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (a, null, true, false, false);
var atop = this.getAtomChiralityLimited (null, a1, pa) - 1;
var ruleA = this.currentRule;
var b2 = Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (b, null, true, false, false);
var btop = this.getAtomChiralityLimited (null, b2, pb) - 1;
var ruleB = this.currentRule;
var c = (atop >= 0 && btop >= 0 ? this.getEneChirality (b2.atoms[btop], b2, a1, a1.atoms[atop], isAxial, true) : 0);
if (c != 0 && (isAxial || !this.bsAtropisomeric.get (a.getIndex ()) && !this.bsAtropisomeric.get (b.getIndex ()))) {
if (isAxial && ((ruleA == 8) != (ruleB == 8))) {
c |= 8;
}a.setCIPChirality (c | ((ruleA - 1) << 5));
b.setCIPChirality (c | ((ruleB - 1) << 5));
if (JU.Logger.debugging) JU.Logger.info (a + "-" + b + " " + JV.JC.getCIPChiralityName (c));
}return c;
}, "JU.SimpleNode,JU.SimpleNode,JU.SimpleNode,JU.SimpleNode,~B");
Clazz.defineMethod (c$, "getEneChirality", 
function (top1, end1, end2, top2, isAxial, allowPseudo) {
return (top1 == null || top2 == null || top1.atom == null || top2.atom == null ? 0 : isAxial ? (this.isPos (top1, end1, end2, top2) ? 18 : 17) : (this.isCis (top1, end1, end2, top2) ? 5 : 6));
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,~B,~B");
Clazz.defineMethod (c$, "isCis", 
function (a, b, c, d) {
JU.Measure.getNormalThroughPoints (a.atom.getXYZ (), b.atom.getXYZ (), c.atom.getXYZ (), this.vNorm, this.vTemp);
var vNorm2 =  new JU.V3 ();
JU.Measure.getNormalThroughPoints (b.atom.getXYZ (), c.atom.getXYZ (), d.atom.getXYZ (), vNorm2, this.vTemp);
return (this.vNorm.dot (vNorm2) > 0);
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "isPos", 
function (a, b, c, d) {
var angle = JU.Measure.computeTorsion (a.atom.getXYZ (), b.atom.getXYZ (), c.atom.getXYZ (), d.atom.getXYZ (), true);
return (angle > 0);
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom");
c$.$CIPChirality$CIPAtom$ = function () {
Clazz.pu$h(self.c$);
c$ = Clazz.decorateAsClass (function () {
Clazz.prepareCallback (this, arguments);
this.id = 0;
this.sphere = 0;
this.rootDistance = 0;
this.isSet = false;
this.isDuplicate = true;
this.isTerminal = false;
this.isAlkene = false;
this.atom = null;
this.atomIndex = 0;
this.bondCount = 0;
this.elemNo = 0;
this.mass = -1;
this.parent = null;
this.h1Count = 0;
this.atoms = null;
this.nAtoms = 0;
this.bsPath = null;
this.myPath = "";
this.oldPriorities = null;
this.priorities =  Clazz.newIntArray (4, 0);
this.oldNPriorities = 0;
this.nPriorities = 0;
this.nRootDuplicates = 0;
this.htPathPoints = null;
this.alkeneParent = null;
this.alkeneChild = null;
this.isAlkeneAtom2 = false;
this.isKekuleAmbiguous = false;
this.nextSP2 = null;
this.multipleBondDuplicate = false;
this.isEvenEne = true;
this.auxEZ = -1;
this.isSP3 = true;
this.auxChirality = '~';
this.nextChiralBranch = null;
this.rootRule4bQueue = null;
this.isChiralPath = false;
this.rule4Type = 0;
this.bsTemp = null;
this.reverseRule2 = false;
this.rule4Ref = 0;
this.bsRS = null;
this.newAtoms = null;
this.rule6refIndex = -1;
Clazz.instantialize (this, arguments);
}, JS.CIPChirality, "CIPAtom", null, [Comparable, Cloneable]);
Clazz.prepareFields (c$, function () {
this.atoms =  new Array (4);
this.bsTemp =  new JU.BS ();
});
Clazz.makeConstructor (c$, 
function () {
});
Clazz.defineMethod (c$, "setupRule6", 
function (a) {
if (this.nPriorities > 2 || (a ? this.countDuplicates (this.atomIndex) : this.nRootDuplicates) <= 2) return 0;
var b = (this.priorities[3] != 1 && !a);
this.b$["JS.CIPChirality"].root.rule6refIndex = this.atoms[this.priorities[2]].atomIndex;
if (b) this.saveRestorePriorities (false);
this.sortSubstituents (-2147483648);
var c = 0;
if (!this.sortSubstituents (0)) return 0;
c = this.checkHandedness ();
if (c == 0 || !b) {
return c;
}this.b$["JS.CIPChirality"].root.rule6refIndex = this.atoms[1].atomIndex;
this.saveRestorePriorities (true);
this.sortSubstituents (-2147483648);
this.sortSubstituents (0);
var d = this.checkHandedness ();
return d == c ? c : 0;
}, "~B");
Clazz.defineMethod (c$, "saveRestorePriorities", 
 function (a) {
if (a) {
this.priorities = this.oldPriorities;
this.nPriorities = this.oldNPriorities;
} else {
this.oldPriorities = java.util.Arrays.copyOf (this.priorities, 4);
this.oldNPriorities = this.nPriorities;
}for (var b = 0; b < this.nAtoms; b++) this.atoms[b].saveRestorePriorities (a);

}, "~B");
Clazz.defineMethod (c$, "countDuplicates", 
 function (a) {
var b = 0;
for (var c = 0; c < 4; c++) {
if (this.atoms[c] == null) continue;
if (this.atoms[c].isDuplicate) {
if (this.atoms[c].atomIndex == a) b++;
} else {
b += this.atoms[c].countDuplicates (a);
}}
return b;
}, "~N");
Clazz.defineMethod (c$, "create", 
function (a, b, c, d, e) {
this.id = ++this.b$["JS.CIPChirality"].ptID;
this.parent = b;
if (a == null) return this;
this.isAlkene = c;
this.atom = a;
this.atomIndex = a.getIndex ();
this.isKekuleAmbiguous = (this.b$["JS.CIPChirality"].bsKekuleAmbiguous != null && this.b$["JS.CIPChirality"].bsKekuleAmbiguous.get (this.atomIndex));
this.elemNo = (d && this.isKekuleAmbiguous ? b.getKekuleElementNumber () : a.getElementNumber ());
this.bondCount = a.getCovalentBondCount ();
this.isSP3 = (this.bondCount == 4 || this.bondCount == 3 && !c && (this.elemNo > 10 || this.b$["JS.CIPChirality"].bsAzacyclic != null && this.b$["JS.CIPChirality"].bsAzacyclic.get (this.atomIndex)));
if (b != null) this.sphere = b.sphere + 1;
if (this.sphere == 1) {
this.htPathPoints =  new java.util.Hashtable ();
} else if (b != null) {
this.htPathPoints = (b.htPathPoints).clone ();
}this.bsPath = (b == null ?  new JU.BS () : JU.BSUtil.copy (b.bsPath));
this.multipleBondDuplicate = d;
this.rootDistance = this.sphere;
if (b == null) {
this.bsPath.set (this.atomIndex);
} else if (this.multipleBondDuplicate && (this.b$["JS.CIPChirality"].rule1bOption == 4 && this.isKekuleAmbiguous || this.b$["JS.CIPChirality"].rule1bOption == 2)) {
} else if (this.multipleBondDuplicate && this.b$["JS.CIPChirality"].rule1bOption == 1) {
this.rootDistance--;
} else if (a === this.b$["JS.CIPChirality"].root.atom) {
d = true;
this.rootDistance = 0;
this.b$["JS.CIPChirality"].root.nRootDuplicates++;
} else if (this.bsPath.get (this.atomIndex)) {
d = true;
this.rootDistance = (e ? b.sphere : this.htPathPoints.get (Integer.$valueOf (this.atomIndex)).intValue ());
} else {
this.bsPath.set (this.atomIndex);
this.htPathPoints.put (Integer.$valueOf (this.atomIndex), Integer.$valueOf (this.rootDistance));
}this.isDuplicate = d;
if (JU.Logger.debuggingHigh) {
if (this.sphere < 50) this.myPath = (b != null ? b.myPath + "-" : "") + this;
JU.Logger.info ("new CIPAtom " + this.myPath);
}return this;
}, "JU.SimpleNode,JS.CIPChirality.CIPAtom,~B,~B,~B");
Clazz.defineMethod (c$, "getMass", 
 function () {
if (this.mass == -1 && (this.mass = this.atom.getMass ()) == Clazz.floatToInt (this.mass)) {
if (this.isType (";4He;16O;52Cr;96Mo;175Lu;")) this.reverseRule2 = true;
 else if (this.elemNo > 92 || this.isType (";9Be;19F;23Na;27Al;31P;45Sc;55Mn;59Co;75As;89Y;93Nb;98Tc;103Rh;127I;133Cs;141Pr;145Pm;159Tb;165Ho;169Tm;197Au;209Bi;209Po;210At;222Rn;223Fr;226Ra;227Ac;231Pa;232Th;and all > U (atomno > 92)")) this.mass = JU.Elements.getAtomicMass (Clazz.floatToInt (this.elemNo));
}return this.mass;
});
Clazz.defineMethod (c$, "isType", 
 function (a) {
return JU.PT.isOneOf (Clazz.floatToInt (this.mass) + JU.Elements.elementSymbolFromNumber (Clazz.floatToInt (this.elemNo)), a);
}, "~S");
Clazz.defineMethod (c$, "getKekuleElementNumber", 
 function () {
var a = this.atom.getEdges ();
var b;
var c = 0;
var d = 0;
for (var e = a.length; --e >= 0; ) if ((b = a[e]).isCovalent ()) {
var f = b.getOtherNode (this.atom);
if (this.b$["JS.CIPChirality"].bsKekuleAmbiguous.get (f.getIndex ())) {
d++;
c += f.getElementNumber ();
}}
return c / d;
});
Clazz.defineMethod (c$, "updateRingList", 
function () {
var a = JU.BSUtil.newAndSetBit (this.atomIndex);
var b = this;
var c = -1;
while ((b = b.parent) != null && c != this.atomIndex) a.set (c = b.atomIndex);

if (a.cardinality () <= 7) {
for (var d = this.b$["JS.CIPChirality"].lstSmallRings.size (); --d >= 0; ) if (this.b$["JS.CIPChirality"].lstSmallRings.get (d).equals (a)) return;

this.b$["JS.CIPChirality"].lstSmallRings.addLast (a);
}});
Clazz.defineMethod (c$, "setNode", 
function () {
if (this.isSet || (this.isSet = true) && this.isDuplicate) return true;
var a = this.atom.getEdges ();
var b = a.length;
if (JU.Logger.debuggingHigh) JU.Logger.info ("set " + this);
var c = 0;
for (var d = 0; d < b; d++) {
var e = a[d];
if (!e.isCovalent ()) continue;
var f = e.getOtherNode (this.atom);
var g = (this.parent != null && this.parent.atom === f);
var h = e.getCovalentOrder ();
if (h == 2) {
if (this.elemNo > 10 || !this.b$["JS.CIPChirality"].isFirstRow (f)) h = 1;
 else {
this.isAlkene = true;
if (g) this.setEne ();
}}if (b == 1 && h == 1 && g) return this.isTerminal = true;
switch (h) {
case 3:
if (this.addAtom (c++, f, g, false, g) == null) return !(this.isTerminal = true);
case 2:
if (this.addAtom (c++, f, h != 2 || g, h == 2, g) == null) return !(this.isTerminal = true);
case 1:
if (g || this.addAtom (c++, f, h != 1 && this.elemNo <= 10, false, false) != null) break;
default:
return !(this.isTerminal = true);
}
}
this.nAtoms = c;
for (; c < this.atoms.length; c++) this.atoms[c] = Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (null, this, false, true, false);

java.util.Arrays.sort (this.atoms);
return true;
});
Clazz.defineMethod (c$, "setEne", 
 function () {
this.parent.alkeneChild = null;
this.alkeneParent = (this.parent.alkeneParent == null ? this.parent : this.parent.alkeneParent);
this.alkeneParent.alkeneChild = this;
this.nextSP2 = this.parent;
if (this.parent.alkeneParent == null) this.parent.nextSP2 = this;
if (this.atom.getCovalentBondCount () == 2 && this.atom.getValence () == 4) {
this.parent.isAlkeneAtom2 = false;
this.alkeneParent.isEvenEne = !this.alkeneParent.isEvenEne;
} else {
this.isAlkeneAtom2 = true;
}});
Clazz.defineMethod (c$, "addAtom", 
function (a, b, c, d, e) {
if (a >= this.atoms.length) {
if (JU.Logger.debugging) JU.Logger.info (" too many bonds on " + this.atom);
return null;
}if (b.getElementNumber () == 1 && b.getIsotopeNumber () == 0) {
if (++this.h1Count > 1) {
if (this.parent == null) {
if (JU.Logger.debuggingHigh) JU.Logger.info (" second H atom found on " + this.atom);
return null;
}}}return this.atoms[a] = Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (b, this, d, c, e);
}, "~N,JU.SimpleNode,~B,~B,~B");
Clazz.defineMethod (c$, "sortSubstituents", 
function (a) {
if (this.b$["JS.CIPChirality"].currentRule != 99 && this.nPriorities == (a < 1 ? 4 : 3)) return true;
var b = (a == -2147483648);
if (b) {
if (this.isTerminal) return false;
switch (this.b$["JS.CIPChirality"].currentRule) {
case 9:
for (var c = 0; c < 4; c++) if (this.atoms[c] != null && !this.atoms[c].isDuplicate && this.atoms[c].atom != null && this.atoms[c].setNode ()) this.atoms[c].sortSubstituents (-2147483648);

break;
case 5:
case 7:
for (var d = 0; d < 4; d++) if (this.atoms[d] != null && this.atoms[d].isChiralPath) this.atoms[d].sortSubstituents (-2147483648);

if (!this.isSP3) return false;
}
}b = new Boolean (b | (this.b$["JS.CIPChirality"].currentRule == 6 || this.b$["JS.CIPChirality"].currentRule == 8)).valueOf ();
var c =  Clazz.newIntArray (4, 0);
var d =  Clazz.newIntArray (4, 0);
if (JU.Logger.debuggingHigh && this.h1Count < 2) {
JU.Logger.info (this.b$["JS.CIPChirality"].root + "---sortSubstituents---" + this);
for (var e = 0; e < 4; e++) {
JU.Logger.info (this.b$["JS.CIPChirality"].getRuleName (this.b$["JS.CIPChirality"].currentRule) + ": " + this + "[" + e + "]=" + this.atoms[e].myPath + " " + Integer.toHexString (this.priorities[e]));
}
JU.Logger.info ("---" + this.nPriorities);
}var e;
var f;
if (this.b$["JS.CIPChirality"].currentRule == 99) for (var g = 0; g < 4; g++) {
var h = this.atoms[g];
if (h.nextChiralBranch != null) {
h.nextChiralBranch.sortSubstituents (a);
}}
for (var h = 0; h < 4; h++) {
var i = this.atoms[h];
for (var j = h + 1; j < 4; j++) {
var k = this.atoms[e = j];
switch (i.atom == null ? 1 : k.atom == null ? -1 : this.priorities[h] < this.priorities[j] ? -1 : this.priorities[j] < this.priorities[h] ? 1 : (f = this.checkPriority (i, k)) != 0 ? f : b ? -2147483648 : this.sign (i.breakTie (k, a + 1))) {
case 1:
e = h;
case -1:
d[e]++;
break;
case 0:
case -2147483648:
break;
}
c[e]++;
}
}
this.bsTemp.clearAll ();
this.newAtoms =  new Array (4);
for (var i = 0; i < 4; i++) {
var j = c[i];
var k = this.newAtoms[j] = this.atoms[i];
if (k.atom != null) this.bsTemp.set (d[i]);
if (this.b$["JS.CIPChirality"].currentRule == 99) continue;
this.priorities[j] = d[i];
}
if (this.b$["JS.CIPChirality"].currentRule == 99) {
return false;
}this.atoms = this.newAtoms;
this.nPriorities = this.bsTemp.cardinality ();
if (JU.Logger.debuggingHigh && this.atoms[2].atom != null && this.atoms[2].elemNo != 1) {
JU.Logger.info (this.dots () + this.atom + " nPriorities = " + this.nPriorities);
for (var j = 0; j < 4; j++) {
JU.Logger.info (this.dots () + this.myPath + "[" + j + "]=" + this.atoms[j] + " " + this.priorities[j] + " " + Integer.toHexString (this.priorities[j]));
}
JU.Logger.info (this.dots () + "-------" + this.nPriorities);
}return (this.nPriorities == this.bondCount);
}, "~N");
Clazz.defineMethod (c$, "dots", 
 function () {
return ".....................".substring (0, Math.min (20, this.sphere));
});
Clazz.defineMethod (c$, "breakTie", 
 function (a, b) {
if (this.isDuplicate && a.isDuplicate && this.atom === a.atom && this.rootDistance == a.rootDistance) return 0;
var c = this.checkIsDuplicate (a);
if (c != 0) return c * (b + 1);
if (!this.setNode () || !a.setNode () || this.isTerminal && a.isTerminal || this.isDuplicate && a.isDuplicate) return 0;
if (this.isTerminal != a.isTerminal) return (this.isTerminal ? 1 : -1) * (b + 1);
if ((c = this.compareShallowly (a, b)) != 0) {
return c;
}this.sortSubstituents (b);
a.sortSubstituents (b);
var d = (this.nAtoms == 0 ? 1 : 0);
var e = 2147483647;
for (var f = 0; f < this.nAtoms; f++) {
var g = this.atoms[f];
var h = a.atoms[f];
if ((c = g.breakTie (h, b + 1)) != 0) {
var i = Math.abs (c);
if (i < e) {
e = i;
d = c;
}}}
return d;
}, "JS.CIPChirality.CIPAtom,~N");
Clazz.defineMethod (c$, "compareShallowly", 
 function (a, b) {
for (var c = 0; c < this.nAtoms; c++) {
var d = this.atoms[c];
var e = a.atoms[c];
var f = d.checkCurrentRule (e);
switch (f) {
case -2147483648:
if (this.b$["JS.CIPChirality"].currentRule != 6) continue;
return -2147483648;
case 0:
continue;
default:
return f * (b + 1);
}
}
return 0;
}, "JS.CIPChirality.CIPAtom,~N");
Clazz.overrideMethod (c$, "compareTo", 
function (a) {
var b;
return (a == null ? -1 : (this.atom == null) != (a.atom == null) ? (this.atom == null ? 1 : -1) : (b = this.checkRule1a (a)) != 0 ? b : (b = this.checkIsDuplicate (a)) != 0 ? b : this.isDuplicate && (b = this.checkRule1b (a)) != 0 ? b : this.checkRule2 (a));
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "checkPriority", 
 function (a, b) {
var c;
return ((a.atom == null) != (b.atom == null) ? (a.atom == null ? 1 : -1) : (c = a.checkCurrentRule (b)) == -2147483648 ? 0 : c);
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "checkIsDuplicate", 
 function (a) {
return a.isDuplicate == this.isDuplicate ? 0 : a.isDuplicate ? -1 : 1;
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "sortByRule", 
 function (a) {
var b = this.b$["JS.CIPChirality"].currentRule;
this.b$["JS.CIPChirality"].currentRule = a;
var c = this.b$["JS.CIPChirality"].root.rule6refIndex;
var d = (a == 9 ? this.setupRule6 (true) != 0 : this.sortSubstituents (0));
this.b$["JS.CIPChirality"].root.rule6refIndex = c;
this.b$["JS.CIPChirality"].currentRule = b;
return d;
}, "~N");
Clazz.defineMethod (c$, "checkCurrentRule", 
 function (a) {
switch (this.b$["JS.CIPChirality"].currentRule) {
default:
case 1:
return this.checkRule1a (a);
case 2:
return this.checkRule1b (a);
case 3:
return this.checkRule2 (a);
case 4:
return this.checkRule3 (a);
case 5:
return this.checkRules4ac (a, " sr SR PM");
case 7:
return this.checkRules4ac (a, " s r p m");
case 6:
case 8:
return this.checkRule4b5 (a);
case 9:
return this.checkRule6 (a);
case 99:
return this.rule4Type == a.rule4Type ? 0 : this.rule4Type == this.b$["JS.CIPChirality"].root.rule4Ref ? -1 : 1;
}
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "checkRule1a", 
 function (a) {
return a.atom == null ? -1 : this.atom == null ? 1 : a.elemNo < this.elemNo ? -1 : a.elemNo > this.elemNo ? 1 : 0;
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "checkRule1b", 
 function (a) {
return a.isDuplicate != this.isDuplicate ? 0 : this.b$["JS.CIPChirality"].rule1bOption == 3 && (this.parent.isAlkene || a.parent.isAlkene) ? 0 : Integer.compare (this.rootDistance, a.rootDistance);
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "checkRule2", 
 function (a) {
return (a.getMass () == this.getMass () ? 0 : (this.reverseRule2 || a.reverseRule2) == (a.mass > this.mass) ? -1 : 1);
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "checkRule3", 
 function (a) {
return this.isDuplicate || a.isDuplicate || !this.parent.isAlkeneAtom2 || !a.parent.isAlkeneAtom2 || !this.parent.alkeneParent.isEvenEne || !a.parent.alkeneParent.isEvenEne || this.parent === a.parent ? 0 : Integer.compare (this.parent.auxEZ, a.parent.auxEZ);
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "checkRules4ac", 
 function (a, b) {
if (this.isTerminal || this.isDuplicate) return 0;
var c = b.indexOf (this.auxChirality);
var d = b.indexOf (a.auxChirality);
return (c > d + 1 ? -1 : d > c + 1 ? 1 : 0);
}, "JS.CIPChirality.CIPAtom,~S");
Clazz.defineMethod (c$, "checkRule4b5", 
 function (a) {
if (this.isTerminal || a.isTerminal) return 0;
var b = this.getBS4b5 ();
var c = this.compareLikeUnlike (b, a.getBS4b5 ());
return (c == null ? -2147483648 : c === b ? -1 : 1);
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "compareLikeUnlike", 
 function (a, b) {
var c = b.clone ();
c.xor (a);
var d = c.nextSetBit (0);
return (d < 0 ? null : a.get (d) ? a : b);
}, "JU.BS,JU.BS");
Clazz.defineMethod (c$, "getBS4b5", 
 function () {
if (this.b$["JS.CIPChirality"].currentRule == 8) return this.bsRS[0];
if (this.bsRS == null) {
this.bsRS =  new Array (2);
this.getBS4bBreadth (1);
this.getBS4bBreadth (2);
}if (JU.Logger.debugging) JU.Logger.info ("getBS4b5 " + this + " " + this.bsRS[0] + this.bsRS[1]);
var a = this.compareLikeUnlike (this.bsRS[0], this.bsRS[1]);
return (a == null ? this.bsRS[0] : a);
});
Clazz.defineMethod (c$, "getBS4bBreadth", 
 function (a) {
this.b$["JS.CIPChirality"].root.rule4Ref = a;
this.b$["JS.CIPChirality"].currentRule = 99;
this.sortSubstituents (0);
this.b$["JS.CIPChirality"].root.rootRule4bQueue.clear ();
this.b$["JS.CIPChirality"].root.rootRule4bQueue.addLast (this);
var b = this.bsRS[a - 1] =  new JU.BS ();
if (this.rule4Type == a) b.set (0);
var c = (this.rule4Type == 0 ? 0 : 1);
while (this.b$["JS.CIPChirality"].root.rootRule4bQueue.size () != 0) {
var d = this.b$["JS.CIPChirality"].root.rootRule4bQueue.removeItemAt (0);
var e = d.newAtoms;
if (e == null) e = d.atoms;
if (e != null) for (var f = 0; f < 4; f++) {
var g = e[f];
if (g == null || g.atom == null || g.isTerminal || g.isDuplicate) continue;
this.b$["JS.CIPChirality"].root.rootRule4bQueue.addLast (g);
if (g.rule4Type == 0) continue;
if (g.rule4Type == a) b.set (c);
c++;
}
}
this.b$["JS.CIPChirality"].currentRule = 6;
}, "~N");
Clazz.defineMethod (c$, "checkRule6", 
 function (a) {
return ((this.atomIndex == this.b$["JS.CIPChirality"].root.rule6refIndex) == (a.atomIndex == this.b$["JS.CIPChirality"].root.rule6refIndex) ? 0 : this.atomIndex == this.b$["JS.CIPChirality"].root.rule6refIndex ? -1 : 1);
}, "JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "getAuxEneWinnerChirality", 
 function (a, b, c, d) {
var e = this.getAuxEneEndWinner (a, a.nextSP2, null);
if (JU.Logger.debuggingHigh) JU.Logger.info (this + " alkene end winner1 " + e);
var f = (e == null || e.atom == null ? null : this.getAuxEneEndWinner (b, b.nextSP2, d));
if (JU.Logger.debuggingHigh) JU.Logger.info (this + " alkene end winners " + e + f);
return this.b$["JS.CIPChirality"].getEneChirality (e, a, b, f, c, false);
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,~B,~A");
Clazz.defineMethod (c$, "getAuxEneEndWinner", 
 function (a, b, c) {
var d = a.clone ();
if (d.parent !== b) d.addReturnPath (b, a);
var e;
for (var f = 1; f <= 9; f++) {
if (d.sortByRule (f)) {
for (var g = 0; g < 4; g++) {
e = d.atoms[g];
if (!e.multipleBondDuplicate) {
if (d.priorities[g] != d.priorities[g + 1]) {
if (c != null) c[0] = f;
return (e.atom == null ? null : e);
}}}
}}
return null;
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,~A");
Clazz.defineMethod (c$, "addReturnPath", 
 function (a, b) {
var c =  new JU.Lst ();
var d = this;
var e;
var f = b;
var g = a;
while (f.parent != null && f.parent.atoms[0] != null) {
if (JU.Logger.debuggingHigh) JU.Logger.info ("path:" + f.parent + "->" + f);
c.addLast (f = f.parent);
}
c.addLast (null);
for (var h = 0, i = c.size (); h < i; h++) {
f = c.get (h);
e = (f == null ? Clazz.innerTypeInstance (JS.CIPChirality.CIPAtom, this, null).create (null, this, this.isAlkene, true, false) : f.clone ());
e.sphere = d.sphere + 1;
d.replaceParentSubstituent (g, a, e);
if (h > 0 && d.isAlkene && !d.isAlkeneAtom2) {
if (a.isAlkeneAtom2) {
a.isAlkeneAtom2 = false;
d.alkeneParent = a;
}d.setEne ();
}a = d;
d = e;
g = b;
b = f;
}
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "replaceParentSubstituent", 
 function (a, b, c) {
for (var d = 0; d < 4; d++) if (this.atoms[d] === a || b == null && this.atoms[d].atom == null) {
if (JU.Logger.debuggingHigh) JU.Logger.info ("reversed: " + b + "->" + this + "->" + c);
this.parent = b;
this.atoms[d] = c;
java.util.Arrays.sort (this.atoms);
break;
}
}, "JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom,JS.CIPChirality.CIPAtom");
Clazz.defineMethod (c$, "createAuxiliaryDescriptors", 
function (a, b) {
var c = false;
var d = '~';
if (this.atom == null) return false;
this.setNode ();
var e = -1;
var f = 0;
var g =  new Array (1);
var h = false;
var i = true;
var j = (!this.isAlkene && this.nPriorities <= (a == null ? 2 : 1));
for (var k = 0; k < 4; k++) {
var l = this.atoms[k];
if (l != null && !l.isDuplicate && !l.isTerminal) {
g[0] = null;
var m = l.createAuxiliaryDescriptors (a == null ? l : a, g);
if (g[0] != null && b != null) b[0] = this.nextChiralBranch = l.nextChiralBranch;
if (l.nextChiralBranch != null || m) {
f++;
c = m;
i = true;
} else {
if (!j && !i && this.priorities[k] == this.priorities[k - 1]) {
return false;
}i = false;
}}}
var l = (f >= 2);
switch (f) {
case 0:
c = false;
case 1:
h = true;
break;
case 2:
case 3:
case 4:
c = false;
if (b != null) b[0] = this.nextChiralBranch = this;
break;
}
if (this.isAlkene) {
if (this.alkeneChild != null) {
if (!this.isEvenEne || (this.auxEZ == 7 || this.auxEZ == -1) && !this.isKekuleAmbiguous && this.alkeneChild.bondCount >= 2) {
var m = (this.isEvenEne ?  Clazz.newIntArray (1, 0) : null);
e = this.getAuxEneWinnerChirality (this, this.alkeneChild, !this.isEvenEne, m);
if (e == 0) {
this.auxEZ = this.alkeneChild.auxEZ = 7;
} else {
if (m != null && m[0] != 8) {
this.auxEZ = this.alkeneChild.auxEZ = e;
if (JU.Logger.debuggingHigh) JU.Logger.info ("alkene type " + this + " " + (this.auxEZ == 6 ? "E" : "Z"));
} else if (!l) {
switch (e) {
case 17:
case 5:
e = 1;
d = 'R';
c = true;
break;
case 18:
case 6:
e = 2;
d = 'S';
c = true;
break;
}
this.auxChirality = d;
this.rule4Type = e;
}}}}} else if (this.isSP3 && b != null) {
var m = this.clone ();
if (m.setNode ()) {
m.addReturnPath (null, this);
var n = 1;
for (; n <= 9; n++) if ((!h || n < 5 || n > 8) && m.sortByRule (n)) break;

if (n > 9) {
d = '~';
} else {
e = m.checkHandedness ();
c = new Boolean (c | (e != 0)).valueOf ();
d = (e == 1 ? 'R' : e == 2 ? 'S' : '~');
if (n == 8) {
d = (d == 'R' ? 'r' : d == 'S' ? 's' : '~');
} else {
this.rule4Type = e;
}}}this.auxChirality = d;
}if (this.b$["JS.CIPChirality"].setAuxiliary && this.auxChirality != '~') this.atom.setCIPChirality (JV.JC.getCIPChiralityCode (this.auxChirality));
if (a == null) this.rule4Type = f;
if (JU.Logger.debugging && d != '~') {
JU.Logger.info ("creating aux " + d + " for " + this + " = " + this.myPath);
}return (this.isChiralPath = c);
}, "JS.CIPChirality.CIPAtom,~A");
Clazz.defineMethod (c$, "checkHandedness", 
function () {
var a = this.atoms[0].atom.getXYZ ();
var b = this.atoms[1].atom.getXYZ ();
var c = this.atoms[2].atom.getXYZ ();
JU.Measure.getNormalThroughPoints (a, b, c, this.b$["JS.CIPChirality"].vNorm, this.b$["JS.CIPChirality"].vTemp);
this.b$["JS.CIPChirality"].vTemp.setT ((this.atoms[3].atom == null ? this.atom : this.atoms[3].atom).getXYZ ());
this.b$["JS.CIPChirality"].vTemp.sub (a);
return (this.b$["JS.CIPChirality"].vTemp.dot (this.b$["JS.CIPChirality"].vNorm) > 0 ? 1 : 2);
});
Clazz.defineMethod (c$, "sign", 
function (a) {
return (a < 0 ? -1 : a > 0 ? 1 : 0);
}, "~N");
Clazz.defineMethod (c$, "addSmallRings", 
function (a) {
if (this.atom == null || this.sphere > 7) return;
if (a != null) a.clear (this.atom.getIndex ());
if (this.isTerminal || this.isDuplicate || this.atom.getCovalentBondCount () > 4) return;
var b;
var c = 0;
var d = this.atom.getEdges ();
for (var e = d.length; --e >= 0; ) {
var f = d[e];
if (!f.isCovalent () || (b = f.getOtherNode (this.atom)).getCovalentBondCount () == 1 || this.parent != null && b === this.parent.atom) continue;
var g = this.addAtom (c++, b, false, false, false);
if (g.isDuplicate) g.updateRingList ();
}
for (var f = 0; f < c; f++) if (this.atoms[f] != null) this.atoms[f].addSmallRings (a);

}, "JU.BS");
Clazz.defineMethod (c$, "clone", 
function () {
var a = null;
try {
a = Clazz.superCall (this, JS.CIPChirality.CIPAtom, "clone", []);
} catch (e) {
if (Clazz.exceptionOf (e, CloneNotSupportedException)) {
} else {
throw e;
}
}
a.id = this.b$["JS.CIPChirality"].ptID++;
a.atoms =  new Array (4);
for (var b = 0; b < 4; b++) a.atoms[b] = this.atoms[b];

a.priorities =  Clazz.newIntArray (4, 0);
a.htPathPoints = this.htPathPoints;
a.alkeneParent = null;
a.auxEZ = -1;
a.rule4Type = 0;
a.bsRS = null;
return a;
});
Clazz.overrideMethod (c$, "toString", 
function () {
return (this.atom == null ? "<null>" : "[" + this.b$["JS.CIPChirality"].currentRule + "." + this.sphere + "," + this.id + "." + this.atom.getAtomName () + (this.isDuplicate ? "*(" + this.rootDistance + ")" : "") + (this.auxChirality == '~' ? "" : "" + this.auxChirality) + "]");
});
c$ = Clazz.p0p ();
};
Clazz.defineStatics (c$,
"RULE_2_nXX_EQ_XX", ";9Be;19F;23Na;27Al;31P;45Sc;55Mn;59Co;75As;89Y;93Nb;98Tc;103Rh;127I;133Cs;141Pr;145Pm;159Tb;165Ho;169Tm;197Au;209Bi;209Po;210At;222Rn;223Fr;226Ra;227Ac;231Pa;232Th;and all > U (atomno > 92)",
"RULE_2_nXX_REV_XX", ";4He;16O;52Cr;96Mo;175Lu;",
"NO_CHIRALITY", 0,
"TIED", 0,
"A_WINS", -1,
"B_WINS", 1,
"IGNORE", -2147483648,
"UNDETERMINED", -1,
"STEREO_R", 1,
"STEREO_S", 2,
"STEREO_M", 17,
"STEREO_P", 18,
"STEREO_Z", 5,
"STEREO_E", 6,
"STEREO_BOTH_RS", 3,
"STEREO_BOTH_EZ", 7,
"RULE_1a", 1,
"RULE_1b", 2,
"RULE_2", 3,
"RULE_3", 4,
"RULE_4a", 5,
"RULE_4b", 6,
"RULE_4c", 7,
"RULE_5", 8,
"RULE_6", 9,
"RULE_RS", 99,
"prefixString", "..........");
c$.zero = c$.prototype.zero = Integer.$valueOf (0);
Clazz.defineStatics (c$,
"ruleNames",  Clazz.newArray (-1, ["", "1a", "1b", "2", "3", "4a", "4b", "4c", "5", "6"]),
"TRIGONALITY_MIN", 0.2,
"MAX_PATH", 50,
"SMALL_RING_MAX", 7,
"RULE_1b_TEST_OPTION_0_UNCHANGED", 0,
"RULE_1b_TEST_OPTION_A_PARENT", 1,
"RULE_1b_TEST_OPTION_B_SELF", 2,
"RULE_1b_TEST_OPTION_C_NONE", 3,
"RULE_1b_TEST_OPTION_D_SELF_KEKULE", 4);
});
