import functools as f
def get_stoich(self):
    stoich = ''
    for i in self:
         if i.isdigit():
            stoich += i
         elif i=='/':
            stoich += i
         else:
             stoich += ':'
    stoich = list((stoich.split(':')))
    while('' in stoich):
        stoich.remove('')
    #display string and floats
    
    stoich_int = [eval(i) for i in stoich]
    stoich_string = stoich
    return(self, stoich_int, stoich_string) 



print(get_stoich('CH6NPbCl3'))
print(get_stoich('C30H28N2PbCl4'))
print(get_stoich('C20H22N2S4Sb(2/3)I4'))
print(get_stoich('C20H22N2S4Sb(3/2)I4'))



