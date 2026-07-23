# Reconstructed no-taper E3/E5 commands
cmd /c 'call <conda_root>/Scripts/activate.bat seismic && python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" setup'
cmd /c 'call <conda_root>/Scripts/activate.bat seismic && python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" manifest'
cmd /c 'call <conda_root>/Scripts/activate.bat seismic && python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" run --experiment e3 --save-tensors'
cmd /c 'call <conda_root>/Scripts/activate.bat seismic && python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" run --experiment e5 --save-tensors --no-deepdenoiser'
cmd /c 'call <conda_root>/Scripts/activate.bat seismic && python "<revision_workspace>\analysis\scripts\reconstruct_e3_e5_no_taper.py" summarize'
