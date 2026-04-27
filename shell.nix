{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.python310Packages.fastapi
    pkgs.python310Packages.uvicorn
    pkgs.python310Packages.pyserial-asyncio
    pkgs.python310Packages.flake8
    pkgs.python310Packages.pydantic
  ];

  shellHook = ''
    echo "--- Protocolo Jarvis Ativo: Ambiente de Desenvolvimento Carregado ---"
  '';
}