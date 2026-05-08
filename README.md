# calx — Financial Calculator Dashboard

A Streamlit dashboard for planning investments and understanding mortgage costs.

## Features

- **Compound Interest** — Calculate growth from a lump-sum investment using annual returns (appropriate for market-traded funds where compounding is reflected in share price)
- **SIP / Regular Contributions** — Model portfolio growth with recurring monthly contributions on top of an initial investment
- **Goal Planner** — Work backwards from a target amount to find the required monthly contribution at a given return rate
- **Mortgage Calculator** — Calculate monthly payments and total interest over the life of a loan; compare a standard repayment schedule against an accelerated one (extra principal per month) to see exactly how much interest and time you save by paying down principal faster

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

```bash
git clone https://github.com/portfola/calx.git
cd calx
pip install -r requirements.txt
```

### Running the app

```bash
streamlit run app.py
```

The dashboard opens automatically in your browser at `http://localhost:8501`.

## Tech Stack

- [Streamlit](https://streamlit.io/) — dashboard framework
- [Plotly](https://plotly.com/python/) — interactive charts
- [Pandas](https://pandas.pydata.org/) / [NumPy](https://numpy.org/) — data handling

## Deployment

The app deploys to **Google Cloud Run** at https://calx.portfola.net. Pushes to `main` build a container, push it to Artifact Registry, and roll out a new Cloud Run revision via GitHub Actions. Cloud Run scales to zero when idle, so steady-state cost is effectively $0 within the free tier.

DNS for `calx.portfola.net` stays in AWS Route53 — only a CNAME is needed there. GitHub Actions authenticates to GCP via Workload Identity Federation (no static service-account keys in the repo).

> **Why Cloud Run and not AWS?** AWS App Runner stopped accepting new customers on 2026-04-30. AWS recommends ECS Express Mode as the replacement, but it auto-provisions an Application Load Balancer (~$16/mo idle) which is overkill for a personal calculator. Cloud Run offers true scale-to-zero and a generous free tier — the right shape for this workload.

### One-time GCP bootstrap

Run these commands once to provision the deployment infrastructure. Set the environment variables first, then run each section in order. You'll need the `gcloud` CLI authenticated as a user with project-creation / IAM admin privileges, plus `aws` for the final Route53 step.

```bash
export GCP_PROJECT_ID=calx-fin      # GCP project (create if needed)
export GCP_REGION=us-central1       # supports Cloud Run domain mappings
export GH_OWNER=portfola            # GitHub org/user
export GH_REPO=calx
export ARTIFACT_REPO=calx
export CLOUD_RUN_SERVICE=calx
export DOMAIN=calx.portfola.net
export PARENT_ZONE=portfola.net
```

#### 1. Create the GCP project (skip if it exists)

```bash
gcloud projects create "$GCP_PROJECT_ID" --name="calx"
gcloud config set project "$GCP_PROJECT_ID"

# Link a billing account (required for Cloud Run, even for free-tier usage):
gcloud billing accounts list
gcloud billing projects link "$GCP_PROJECT_ID" --billing-account=<BILLING_ACCOUNT_ID>
```

#### 2. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com
```

#### 3. Artifact Registry repository

```bash
gcloud artifacts repositories create "$ARTIFACT_REPO" \
  --repository-format=docker \
  --location="$GCP_REGION" \
  --description="calx container images"
```

#### 4. Service account for GitHub Actions

A dedicated service account with least-privilege roles for this repo only.

```bash
gcloud iam service-accounts create calx-github-deploy \
  --display-name="GitHub Actions deploy for calx"

export SA_EMAIL="calx-github-deploy@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# Push images to Artifact Registry
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# Deploy and update Cloud Run services
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

# Allow this SA to act as the Cloud Run runtime service account
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"
```

#### 5. Workload Identity Federation (the GCP equivalent of AWS OIDC)

```bash
# Pool
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions"

export POOL_ID=$(gcloud iam workload-identity-pools describe github-pool \
  --location=global --format='value(name)')

# Provider — restricted to this repo only
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub Actions OIDC" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository == '${GH_OWNER}/${GH_REPO}' && assertion.ref == 'refs/heads/main'"

export PROVIDER_NAME=$(gcloud iam workload-identity-pools providers describe github-provider \
  --location=global --workload-identity-pool=github-pool --format='value(name)')

# Allow the GitHub repo to impersonate the SA
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${GH_OWNER}/${GH_REPO}"

echo "WIF provider (paste into GCP_WIF_PROVIDER repo var): $PROVIDER_NAME"
```

#### 6. Initial image build and Cloud Run service

Cloud Run needs an existing image to deploy from, so push one before creating the service.

```bash
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet

export IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REPO}/calx:initial"
docker build -t "$IMAGE" .
docker push "$IMAGE"

gcloud run deploy "$CLOUD_RUN_SERVICE" \
  --image="$IMAGE" \
  --region="$GCP_REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8501 \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=0 \
  --max-instances=2 \
  --timeout=3600 \
  --concurrency=80
```

The `--timeout=3600` allows long-lived WebSocket connections (Streamlit uses them for widget updates). `--min-instances=0` enables scale-to-zero.

#### 7. Custom domain (calx.portfola.net)

**Verify the parent domain** with Google first (one-time, per parent domain). `gcloud domains verify` only tries to open Search Console in a browser — it doesn't perform the verification itself. On WSL/headless shells the browser-open fails (`gio: ... Operation not supported`); just open the URL manually:

```
https://search.google.com/search-console/welcome?new_domain_name=portfola.net
```

In Search Console, choose the **Domain** property type and enter `portfola.net`. Google will give you a TXT record like `google-site-verification=<token>`. Add it to Route53, then click **Verify** in Search Console:

```bash
ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name "$PARENT_ZONE" \
  --query 'HostedZones[0].Id' --output text)

# Replace <token> with the value Search Console shows you
cat > /tmp/calx-verify.json <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${PARENT_ZONE}.",
      "Type": "TXT",
      "TTL": 300,
      "ResourceRecords": [{ "Value": "\"google-site-verification=<token>\"" }]
    }
  }]
}
EOF

aws route53 change-resource-record-sets \
  --hosted-zone-id "$ZONE_ID" \
  --change-batch file:///tmp/calx-verify.json
```

Wait ~1 minute for DNS to propagate, then click Verify in Search Console. Confirm gcloud sees the verification before continuing:

```bash
gcloud domains list-user-verified
```

Once `portfola.net` shows up there, create the domain mapping:

```bash
gcloud beta run domain-mappings create \
  --service="$CLOUD_RUN_SERVICE" \
  --domain="$DOMAIN" \
  --region="$GCP_REGION"

# Fetch the DNS records you need to add (CNAME target + any validation records):
gcloud beta run domain-mappings describe \
  --domain="$DOMAIN" \
  --region="$GCP_REGION" \
  --format='value(status.resourceRecords)'
```

That output gives you a CNAME (typically `ghs.googlehosted.com`) for `calx.portfola.net`. Add it to Route53 (`ZONE_ID` is already set from the verification step above):

```bash
cat > /tmp/calx-r53.json <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "${DOMAIN}.",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{ "Value": "ghs.googlehosted.com." }]
    }
  }]
}
EOF

aws route53 change-resource-record-sets \
  --hosted-zone-id "$ZONE_ID" \
  --change-batch file:///tmp/calx-r53.json
```

Cloud Run will provision and attach a managed TLS cert automatically once DNS resolves. Check status:

```bash
gcloud beta run domain-mappings describe \
  --domain="$DOMAIN" \
  --region="$GCP_REGION" \
  --format='value(status.conditions)'
```

#### 8. GitHub repository variables

Set these as repo **variables** (not secrets — none are sensitive). Requires gh ≥ 2.28. `--repo` is passed explicitly because `GH_REPO` is a gh-reserved env var that expects the full `OWNER/REPO` form, and the bootstrap sets it to just `calx`.

```bash
REPO="$GH_OWNER/$GH_REPO"
gh variable set GCP_PROJECT_ID       --repo "$REPO" --body "$GCP_PROJECT_ID"
gh variable set GCP_REGION           --repo "$REPO" --body "$GCP_REGION"
gh variable set GCP_WIF_PROVIDER     --repo "$REPO" --body "$PROVIDER_NAME"
gh variable set GCP_SERVICE_ACCOUNT  --repo "$REPO" --body "$SA_EMAIL"
gh variable set ARTIFACT_REPO        --repo "$REPO" --body "$ARTIFACT_REPO"
gh variable set CLOUD_RUN_SERVICE    --repo "$REPO" --body "$CLOUD_RUN_SERVICE"
```

### Deploying

After the bootstrap is complete, every push to `main` deploys automatically. To deploy manually without a code change:

```bash
gcloud run deploy "$CLOUD_RUN_SERVICE" \
  --image="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REPO}/calx:latest" \
  --region="$GCP_REGION"
```

### Rollback

Cloud Run keeps every revision. List them and route 100% of traffic back to a previous one:

```bash
gcloud run revisions list --service="$CLOUD_RUN_SERVICE" --region="$GCP_REGION"

gcloud run services update-traffic "$CLOUD_RUN_SERVICE" \
  --region="$GCP_REGION" \
  --to-revisions=<previous-revision-name>=100
```
