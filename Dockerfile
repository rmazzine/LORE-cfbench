FROM python:3.7.14-bullseye

ADD ./. /lore/
WORKDIR /lore/benchmark/
RUN python3 -m pip install -r requirements_exp.txt

CMD python3 run_exp.py && until python3 -c "from cfbench.cfbench import analyze_results; analyze_results('lore')"; do sleep 10; done