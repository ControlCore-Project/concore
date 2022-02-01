function result=controller(ym)
  global ysp;
  if ym(1) < ysp
     result = 1.01 * ym;
  else
     result = 0.9 * ym;
  end
end

