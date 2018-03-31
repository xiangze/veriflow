Veriflow

tensorflow-like verilog generator/executor

sample
    	import veriflow as tf
	a=vf.Input("a")
	b=vf.Input("b")
	c=vf.add(a,b)
	cr=vf.Reg("cr",c)
	with vf.Session() as s:
	     s.run(cr,{a:1,b:2})

