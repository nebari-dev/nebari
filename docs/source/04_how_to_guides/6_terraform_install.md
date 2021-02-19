## How can I downgrade an installed Terraform version?

QHub is currently compatible with Terraform version 0.13.5. To check your installed version on terminal type `terrafrom -v`.
If your local version is more recent than the recommended, follow the steps:
On terminal type `which terraform` to find out where the binary installation file is located.
The output will be a filepath, such as: `/usr/bin/terraform`
Then, remove the binary file with:
```shell
rm -r /usr/bin/terraform
```
> `/usr/bin/terraform` corresponds to the location of the installed binary file.

Next, download the binary for the compatible version with:
```shell
wget https://releases.hashicorp.com/terraform/0.13.5/
```
Unzip the file, and move it to the same location as the previous one:
```shell
unzip terraform_0.13.5
mv ~/Downloads/terraform /usr/bin/
```
Finally, check if the correct version was installed with `terraform -v`, the output should be `Terraform v0.13.5`.