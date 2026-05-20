#!/usr/bin/env bash
PYTHON="/c/Users/prsid/.conda/envs/passportos/python.exe"
DIR="$(cd "$(dirname "$0")" && pwd)"

export PYTHONIOENCODING=utf-8

echo ""
echo "  PassportOS"
echo "  ----------"
echo "  1) Battery DPP"
echo "  2) Solar Passport"
echo "  3) Both"
echo ""
read -rp "  Choose [1-3]: " choice

$PYTHON "$DIR/mock_erp_api.py" &
ERP_PID=$!
PIDS="$ERP_PID"

case $choice in
  1)
    $PYTHON -m streamlit run "$DIR/dpp_erp_prototype/app_v2.py" --server.port 8501 &
    PIDS="$PIDS $!"
    echo ""
    echo "  ERP API     -> http://localhost:5000"
    echo "  Battery DPP -> http://localhost:8501"
    ;;
  2)
    $PYTHON -m streamlit run "$DIR/pv_prototype/pv_app.py" --server.port 8502 &
    PIDS="$PIDS $!"
    echo ""
    echo "  ERP API    -> http://localhost:5000"
    echo "  Solar DPP  -> http://localhost:8502"
    ;;
  3)
    $PYTHON -m streamlit run "$DIR/dpp_erp_prototype/app_v2.py" --server.port 8501 &
    PIDS="$PIDS $!"
    $PYTHON -m streamlit run "$DIR/pv_prototype/pv_app.py" --server.port 8502 &
    PIDS="$PIDS $!"
    echo ""
    echo "  ERP API     -> http://localhost:5000"
    echo "  Battery DPP -> http://localhost:8501"
    echo "  Solar DPP   -> http://localhost:8502"
    ;;
  *)
    echo "Invalid choice, exiting."
    kill $ERP_PID 2>/dev/null
    exit 1
    ;;
esac

echo ""
echo "  Ctrl+C to stop everything"

trap "kill $PIDS 2>/dev/null; exit" INT TERM
wait
