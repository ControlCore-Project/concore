@echo off
if dummy%~n2 == dummy (
 if dummy%~x1 == dummy.graphml (
 echo python mkconcore.py %~d1%~p1%~n1%~x1 %~d1%~p1 %~n1 docker
      python mkconcore.py %~d1%~p1%~n1%~x1 %~d1%~p1 %~n1 docker
 ) else (
 echo python mkconcore.py %~d1%~p1%~n1.graphml %~d1%~p1 %~n1 docker
      python mkconcore.py %~d1%~p1%~n1.graphml %~d1%~p1 %~n1 docker
 )
) else (
 if dummy%~x1 == dummy.graphml (
 echo python mkconcore.py %~d1%~p1%~n1%~x1 %~d1%~p1 %~n2 docker
      python mkconcore.py %~d1%~p1%~n1%~x1 %~d1%~p1 %~n2 docker
 ) else (
 echo python mkconcore.py %~d1%~p1%~n1.graphml %~d1%~p1 %~n2 docker
      python mkconcore.py %~d1%~p1%~n1.graphml %~d1%~p1 %~n2 docker
 )
)