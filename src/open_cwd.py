def open():
	import os
	cwd = os.getcwd()
	os.system("explorer "+cwd)

#label1 = Button(self, text="Pre TC", fg="red", font=("Ariel", 9, "bold"), command=open)