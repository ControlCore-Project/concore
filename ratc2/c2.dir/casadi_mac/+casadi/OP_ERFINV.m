function v = OP_ERFINV()
  persistent vInitialized;
  if isempty(vInitialized)
    vInitialized = casadiMEX(0, 90);
  end
  v = vInitialized;
end
