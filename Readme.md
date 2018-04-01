# Veriflow
tensorflow-like verilog generator/executor


sample:
------

	import veriflow as tf
	
	a=vf.Input("a")
	b=vf.Input("b")
	c=vf.add(a,b)
	cr=vf.Reg("cr",c)
	o=vf.Output("o",cr)
	with vf.Session() as s:
	     s.run(o,{a:1,b:2})

