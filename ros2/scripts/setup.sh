script_dir="$(dirname "$(realpath "${BASH_SOURCE[-1]:-${(%):-%x}}")")"
source $script_dir/env.sh

source $VENV_DIR/bin/activate
source $WS_DIR/install/setup.sh

export PYTHONPATH=$PYTHONPATH:$VENV_DIR/lib/python3.8/site-packages