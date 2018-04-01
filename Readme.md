# Veriflow
tensorflow-like verilog generator/executor

requirement
------
[verilator](https://www.veripool.org/wiki/verilator) or [iverilog](http://iverilog.icarus.com/)


sample:
------
```python
	import veriflow as vf
	
	a=vf.Input("a")
	b=vf.Input("b")
	c=vf.add(a,b)
	cr=vf.Reg("cr",c)
	o=vf.Output("o",cr)
	with vf.Session() as s:
	     s.run(o,{a:1,b:2})
```
