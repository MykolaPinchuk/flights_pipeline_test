# yes | conda create -n python38 python=3.8
# conda activate python38
# conda install ipykernel
# ipython kernel install --name="python38" --user

VENV=py38

# create new env in `$HOME`
conda create -y -q -p $HOME/conda_env/$VENV python=3.8 ipykernel

# activate env
source /opt/conda/bin/activate ~/conda_env/$VENV

# register kernel to `$HOME/.local/share/jupyter/kernels`, so it will be preserved
python -m ipykernel install --user --name $VENV

# install your packages, WITHOUT `--user`
pip install numpy==1.22

# check package installation path
pip list -v
