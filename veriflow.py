import os

debug=False

def _dprint(s):
    if(debug):print(s)

def _gendefs(name,sp,shape=[],bits=8,issigned=False,end=";"):
    dim=len(shape)

    if(dim==0):
        return "%s [%d:0] %s%s"%(sp,bits-1,name,end)
    elif(dim==1):
        return "%s [%d:0][%d:0] %s%s"%(sp,bits-1,shape[0]-1,name,end)
    elif(dim==2):
        return "%s [%d:0][%d:0][%d:0] %s%s"%(sp,bits-1,shape[0]-1,shape[1]-1,name,end)
    else:
        return "%s [%d:0][%d:0][%d:0][%d:0] %s%s"%(sp,bits-1,shape[0]-1,shape[1]-1,shape[2]-1,name,end)

class Variable(object):
    def gendefs(self,name,sp,shape=[],bits=8,issigned=False,end=";"):
        return _gendefs(name,sp,shape,bits,issigned,end)

    def __init__(self,name,sp,shape=[],bits=8,issigned=False,end=";"):
        self.dim=len(shape)
        self.name=name
        self.shape=shape
        self.width=bits
        self.bits=bits
        self.issigned=issigned
        self.issigned=issigned
        self.defs=self.gendefs(name,sp,shape,bits,issigned,end)
        self.s=""
        self.leaf=[]

    def dump(self):
        print('name:'+self.name)
        print('type:'+str(type(self)))
        print('def :'+self.defs)
        print('ss  :'+self.s)
        print('leaf  :')
        print(self.leaf)
        for l in self.leaf:
            l.dump()

class Wire(Variable):        
    def __init__(self,name,ops=None,shape=[],bits=8,issigned=False):
        super().__init__(name,"wire",shape,bits,issigned)
        if(ops!=None):
            self.s="assign %s=%s;"%(name,ops.s)
            self.leaf=ops["leaf"]

class Reg(Variable):        
    def __init__(self,name,conds_values,shape=[],bits=8,issigned=False,latency=1):
        super().__init__(name,"reg",shape,bits,issigned)

        self.s="always(posedge clock org negedge resetn)begin\n"
        self.s+="%s <='0;\n"%name
        if(type(conds_values)==list):#[condition::s:value::{s:leaf} ]
            self.leaf=[]
            for conds_values in conds_values:
                for k,v in conds_value.items():
                    self.s+="end else if (%s)begin\n"%k
                    self.s+="%s <=%s;\n"%(name,v.s)
                    self.leaf.appends(v)
        else:#op::{s:leaf}
            self.s+="end else begin\n"
            self.s+="%s <=%s;\n"%(name,conds_values["s"])
            self.leaf=conds_values["leaf"]
        self.s+="end\n"


class Input(Variable):        
    def __init__(self,name,shape=[],bits=8,issigned=False):
        super().__init__(name,"input",shape,bits,issigned,"")

    def putreg(self):
        return _gendefs(self.name,"reg",self.shape,self.bits,self.issigned,";")

class Output(Variable):        
    def __init__(self,name,ops,shape=[],bits=8,issigned=False):
        super().__init__(name,"output",shape,bits,issigned,"")
        self.s="assign %s=%s;"%(name,ops.s)
        self.leaf=ops["leaf"]

    def putwire(self):
        return _gendefs(self.name,"wire",self.shape,self.bits,self.issigned,";")

def op2(op,l,r):
    s="%s %s %s"%(l.name,op,r.name)
    return {"s":s,"leaf":[l,r]}

def add(l,r):
    return op2("+",l,r)

def sub(l,r):
    return op2("-",l,r)

def multiply(l,r):
    return op2("*",l,r)

def _getinputs1(t,ins=[]):
    if(isinstance(t,Input)):
        ins.append(t)
        _dprint("getinputs input")
    elif(isinstance(t,list)):
        _dprint("getinputs list")
        _dprint(ins)
        for l in t:
            ins=_getinputs1(l,ins)
    else:
        _dprint("getinputs leaf")
        ins=_getinputs1(t.leaf,ins)
    return ins

def _getinputs(t,ins=[]):
    return list(set(_getinputs1(t,ins)))

def _getoutputs1(t,ins=[]):
    if(isinstance(t,Output)):
        ins.append1(t)
        _dprint("getoutputs output")
    elif(isinstance(t,list)):
        _dprint("getoutputs list")
        _dprint(ins)
        for l in t:
            ins=_getoutputs1(l,ins)
    else:
        _dprint("getoutputs leaf")
        ins=_getoutputs1(t.leaf,ins)
    return ins

def _getoutputs(t,ins=[]):
    return list(set(_getoutputs1(t,ins)))

def _flatten(ls):
    flist=[]
    lls=[ls]
    while(len(lls)>0):
        node=lls.pop(0)
        if(isinstance(node,list)):
            lls=node+lls
        else:
            flst.append(node)

class Session(object):
   def __init__(self,sim="iverilog",ifname="test.sv",modname="testmod.sv"):
       self.simulator=sim
       self.ifname=ifname
       self.clock="clock"
       self.reset="resetn"

       self.modname=modname
       self.modnametr=modname.split(".")[0]
       self.vars=[]
       self.seq=""
       self.s=""

   def _ckp(self):
       return """
       initial begin
       %s = 0;
       forever begin
       #5 %s = ~%s;
        end
      end\n"""%(self.clock,self.clock,self.clock)

   def _resetp(self):
       return """
       initial begin
       %s = 0;
       #1
       %s = 1;
       end\n"""%(self.reset,self.reset)

   def __mod(self,vars):
       s="module %s(\n"%(self.modnametr)
       ios=_getinputs(vars)
       ios+=_getoutputs(vars)
       s+=",\n".join([i.defs for i in ios])
       s+=");\n"

       s+="\n".join([v.defs for v in vars])  
       s+="\n"
       s+="\n".join([v.s for v in vars])  
       s+="\n"
       s+="endmodule\n"
       return s

   def _inst(self,vars,suf=""):
       ios=_getinputs(vars)
       ios+=_getoutputs(vars)
       s="%s %s_%s("%(self.modnametr,self.modnametr,suf)+"\n"
       s+=".%s (%s),"%(self.clock,self.clock)+"\n"
       s+=".%s (%s),"%(self.reset,self.reset)+"\n"
       s+=",".join([ ".%s (%s%s)\n"%(i.name,i.name,suf) for i in ios ])
       s+=");\n"
       return s

   def run(self,f,feed_dict,wait=1):
       self.vars.append(f)
       ins=_getinputs([f])

       _dprint("*run::")
       _dprint("inputs::")
       _dprint(ins)
       _dprint("vars:")
       _dprint(self.vars)

       for k,v in feed_dict.items():
           for i in ins:
               if(k==i.name):
                   self.seq+="%s =%s;\n"%(i.name,v)
                   if(wait>0):
                       self.seq+="repeat(%d)@posedge(%s);\n"%(wait,clock)

   def __enter__(self):
       return self

   def __exit__(self, exc_type, exc_value, traceback):
       _dprint("*exit")
       _dprint("vars:")
       _dprint(self.vars)

#module
       self.fp=open(self.modname,'w')
       self.fp.write(self.__mod(self.vars))
       self.fp.close()
#test
       self.s="module test();\n"
       self.s+="reg %s,%s;\n"%(self.clock,self.reset)

       for i in _getinputs(self.vars):
           self.s+=i.putreg();
       for o in _getoutputs(self.vars):
           self.s+=o.putwire();
##sequence
       self.s+="initial begin\n"
       self.s+=self.seq
       for o in _getoutputs(self.vars):
           self.s+="$display(\"%%d\",%%%s);\n"%o.name           

       self.s+="$finish();\n"
       self.s+="end\n"
       
       self.s+=self._ckp()
       self.s+=self._resetp()
       self.s+=self._inst(self.vars)
       self.s+="endmodule\n"

       self.fs=open(self.ifname,'w')
       self.fs.write(self.s)
       self.fs.close()

       try:
           if(self.simulator=="iverilog"):
               os.system("iverilog -o %s *.sv "%ifname)
               os.system("vvp %s"%ifname)
           elif(self.simulator=="verilator"):
               os.system("verilator --cc -Wno-lint %s --exe sim_verilator/test.cpp"%(ifname))
               os.system("cd obj_dir && make -j -f %s.mk %s && cd ../"%(ifname,ifname))
               os.system("./"+ifname)
           else:
               print("not supported simulator.")
               raise Exception
       except:
               print("tool is not installed or doesnt work.")


if __name__=='__main__':
#   debug=True
   a=Input("a")
   b=Input("b")
   c=add(a,b)
   cr=Reg("cr",c)
#   cr.dump()

   with Session() as ses:
       ses.run(cr,{a:1,b:2})

