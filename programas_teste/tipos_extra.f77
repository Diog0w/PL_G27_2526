program tipos_extra
real x, y
character c
logical a, b
integer p
! Teste extra: tipos REAL/CHARACTER, operadores logicos e END IF.
x = 1
y = 2.5
c = 'A'
a = .not. .false.
b = a .or. (x .lt. y)
p = 2 ** 3
if ((p .ne. 7) .and. (y .ge. x)) then
print *, c, x, y, p
end if
stop
end
