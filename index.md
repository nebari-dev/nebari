# QHUB Documentation

![](https://avatars0.githubusercontent.com/u/34879953?v=4&s=200)

> Open source tooling for data science research, development, and deployment.

Qhub is [__Infrastructure as Code__](#What-is-Infrastructure-as-Code.) 
simplifies the deployment of data science infrastructure for you and your team.

```{toctree}
index
docs/getting-started
docs/faqs
```

![](https://avatars1.githubusercontent.com/u/17131925?v=4&s=100)![](https://avatars2.githubusercontent.com/u/17927519?v=4&s=100)![](https://avatars1.githubusercontent.com/u/5429470?v=4&s=100)![](https://avatars2.githubusercontent.com/u/288277?v=4&s=100)
    
## Use the Qhub wizard for your favorite service.
    
The Qhub wizard will ask you a few questions to help you
get started on a long journey with data science. We'll ask you a 
few questions.
    
## Try Qhub for free on ![](https://avatars0.githubusercontent.com/u/4650108?v=4&s=60)
    
### Or customize your Qhub service

![](https://avatars0.githubusercontent.com/u/4650108?v=4&s=100)![](https://avatars3.githubusercontent.com/u/2232217?v=4&s=100)![](https://avatars0.githubusercontent.com/u/2810941?v=4&s=100)
    
### Digital Ocean Options
    
Choose the specifications for your nodes and workers from the list below. 
    
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>memory</th>
      <th>vcpus</th>
      <th>disk</th>
      <th>price_hourly</th>
      <th>price_monthly</th>
      <th>managed_hourly</th>
      <th>managed_weekly</th>
    </tr>
    <tr>
      <th>slug</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>s-1vcpu-1gb</th>
      <td>1024</td>
      <td>1</td>
      <td>25</td>
      <td>0.00744</td>
      <td>5.0</td>
      <td>0.01</td>
      <td>0.6</td>
    </tr>
    <tr>
      <th>s-3vcpu-1gb</th>
      <td>1024</td>
      <td>3</td>
      <td>60</td>
      <td>0.02232</td>
      <td>15.0</td>
      <td>0.03</td>
      <td>1.8</td>
    </tr>
    <tr>
      <th>s-1vcpu-2gb</th>
      <td>2048</td>
      <td>1</td>
      <td>50</td>
      <td>0.01488</td>
      <td>10.0</td>
      <td>0.02</td>
      <td>1.2</td>
    </tr>
    <tr>
      <th>s-2vcpu-2gb</th>
      <td>2048</td>
      <td>2</td>
      <td>60</td>
      <td>0.02232</td>
      <td>15.0</td>
      <td>0.03</td>
      <td>1.8</td>
    </tr>
    <tr>
      <th>s-1vcpu-3gb</th>
      <td>3072</td>
      <td>1</td>
      <td>20</td>
      <td>0.02232</td>
      <td>15.0</td>
      <td>0.03</td>
      <td>1.8</td>
    </tr>
    <tr>
      <th>s-2vcpu-4gb</th>
      <td>4096</td>
      <td>2</td>
      <td>80</td>
      <td>0.02976</td>
      <td>20.0</td>
      <td>0.04</td>
      <td>2.4</td>
    </tr>
    <tr>
      <th>s-4vcpu-8gb</th>
      <td>8192</td>
      <td>4</td>
      <td>160</td>
      <td>0.05952</td>
      <td>40.0</td>
      <td>0.09</td>
      <td>5.4</td>
    </tr>
    <tr>
      <th>s-6vcpu-16gb</th>
      <td>16384</td>
      <td>6</td>
      <td>320</td>
      <td>0.11905</td>
      <td>80.0</td>
      <td>0.18</td>
      <td>10.8</td>
    </tr>
    <tr>
      <th>s-8vcpu-32gb</th>
      <td>32768</td>
      <td>8</td>
      <td>640</td>
      <td>0.23810</td>
      <td>160.0</td>
      <td>0.36</td>
      <td>21.6</td>
    </tr>
    <tr>
      <th>s-12vcpu-48gb</th>
      <td>49152</td>
      <td>12</td>
      <td>960</td>
      <td>0.35714</td>
      <td>240.0</td>
      <td>0.54</td>
      <td>32.4</td>
    </tr>
    <tr>
      <th>s-16vcpu-64gb</th>
      <td>65536</td>
      <td>16</td>
      <td>1280</td>
      <td>0.47619</td>
      <td>320.0</td>
      <td>0.71</td>
      <td>42.6</td>
    </tr>
    <tr>
      <th>s-20vcpu-96gb</th>
      <td>98304</td>
      <td>20</td>
      <td>1920</td>
      <td>0.71429</td>
      <td>480.0</td>
      <td>1.07</td>
      <td>64.2</td>
    </tr>
    <tr>
      <th>s-24vcpu-128gb</th>
      <td>131072</td>
      <td>24</td>
      <td>2560</td>
      <td>0.95238</td>
      <td>640.0</td>
      <td>1.43</td>
      <td>85.8</td>
    </tr>
    <tr>
      <th>s-32vcpu-192gb</th>
      <td>196608</td>
      <td>24</td>
      <td>3840</td>
      <td>1.42857</td>
      <td>960.0</td>
      <td>2.14</td>
      <td>128.4</td>
    </tr>
  </tbody>
</table>
    
> We would have some recommendation.
> Which of these are free teir? 
> Can we replace this with our own processing.
    
### Environment Bundle
    
Environment bundles are curated collections of domain specific 
computing tools.
    
- [x] Data Science
- [ ] GPU
- [ ] Geospatial
- [ ] Financial services
- [x] Teaching
- [ ] Space
- [ ] Developer
    
### Invite users to your hub?
    
<input value="tonyfast ani"></input>
## For command line users

If you prefer, Qhub is configurable from the command line.  Learn more about the CLIs
    
```bash
qhub new Myhub --workers 10 --users 4
qhub new -f myhub.yaml
```
    
### Why QHUB?
    
There are many steps along the lifecycle of data science products. Qhub is designed 
to work at all points in the process. It includes jupyterlab, dask, kubernetes
    
### What is __Infrastructure as Code__.

```{toctree}
:hidden: true
:maxdepth: 2
```<!--

    [NbConvertApp] Converting notebook readme.md.ipynb to markdown

-->