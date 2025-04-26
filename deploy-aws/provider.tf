terraform {

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "urada-timechain-deploy"
    key    = "terraform/deployments/terraform.tfstate"
    region = "us-east-2"
  }
}


# Configure the AWS Provider
provider "aws" {
  region = "us-east-2"
}

