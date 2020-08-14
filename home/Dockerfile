FROM continuumio/miniconda3:latest
COPY ./app /app
RUN conda init
RUN conda create -n fast_api 
RUN echo "conda activate fast_api" > ~/.bashrc
RUN conda install  -c conda-forge fastapi pydantic uvicorn -y
ENV PATH /opt/conda/envs/fast_api/bin:$PATH
WORKDIR app/
EXPOSE 8000
CMD ["uvicorn", "main:fastapi", "--host", "0.0.0.0", "--port", "8000"]
