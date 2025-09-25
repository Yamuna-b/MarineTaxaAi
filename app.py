import io
from pathlib import Path
import streamlit as st
from PIL import Image, ImageDraw
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Optional dependency: networkx (fallback to placeholder if missing)
try:
	import networkx as nx
	_HAS_NX = True
except Exception:
	_HAS_NX = False


st.set_page_config(page_title="MarineTaxaAI", page_icon="🌊", layout="wide")

# Note: For large file uploads, create a .streamlit/config.toml file with:
# [server]
# maxUploadSize = 5000


# Session state defaults
if "single_sequence" not in st.session_state:
	st.session_state["single_sequence"] = ""
if "mode" not in st.session_state:
	st.session_state["mode"] = "user"  # user | research
if "analysis_trigger" not in st.session_state:
	st.session_state["analysis_trigger"] = False
if "uploaded_files" not in st.session_state:
	st.session_state["uploaded_files"] = []
if "dive_depth" not in st.session_state:
	st.session_state["dive_depth"] = 0
if "auto_dive" not in st.session_state:
	st.session_state["auto_dive"] = False


# Reusable helpers

def make_placeholder(text: str, size=(900, 420)):
	img = Image.new("RGB", size, color=(10, 24, 36))
	draw = ImageDraw.Draw(img)
	draw.rectangle([8, 8, size[0]-8, size[1]-8], outline=(90, 169, 255))
	draw.text((24, size[1]//2 - 12), f"{text}", fill=(200, 210, 220))
	return img


# Sample taxa hierarchy for sunburst/treemap
USER_TAXA_ROWS = [
	{"kingdom": "Animalia", "phylum": "Chordata", "class": "Actinopterygii", "order": "Perciformes", "family": "Pomacentridae", "genus": "Amphiprion", "species": "A. ocellaris", "reads": 3200},
	{"kingdom": "Animalia", "phylum": "Mollusca", "class": "Cephalopoda", "order": "Oegopsida", "family": "Architeuthidae", "genus": "Architeuthis", "species": "A. dux", "reads": 560},
	{"kingdom": "Animalia", "phylum": "Arthropoda", "class": "Malacostraca", "order": "Decapoda", "family": "Caridea", "genus": "Shrimp sp.", "species": "", "reads": 1980},
]


def user_taxa_sunburst():
	df = pd.DataFrame(USER_TAXA_ROWS)
	fig = px.sunburst(
		df,
		path=["kingdom", "phylum", "class", "order", "family", "genus", "species"],
		values="reads",
		color="reads",
		color_continuous_scale="Blues",
		title="Interactive Taxonomic Sunburst (click to drill down)",
	)
	fig.update_layout(margin=dict(t=40,l=0,r=0,b=0), template="plotly_dark")
	return fig


def research_network_graph():
	if not _HAS_NX:
		fig = go.Figure()
		fig.add_annotation(text="Install networkx to see relationship network", showarrow=False, font=dict(color="#9aa0a6"))
		fig.update_layout(template='plotly_dark', height=320)
		return fig
	G = nx.Graph()
	G.add_nodes_from(["A. ocellaris","Architeuthis dux","Shrimp sp.","C. leucas"]) 
	G.add_edge("A. ocellaris","Shrimp sp.", weight=0.3)
	G.add_edge("Architeuthis dux","Shrimp sp.", weight=0.2)
	G.add_edge("C. leucas","A. ocellaris", weight=0.1)
	pos = nx.spring_layout(G, seed=7)
	x, y, text = [], [], []
	for n in G.nodes:
		x.append(pos[n][0]); y.append(pos[n][1]); text.append(n)
	edges_x, edges_y = [], []
	for (u,v,w) in G.edges(data=True):
		edges_x += [pos[u][0], pos[v][0], None]
		edges_y += [pos[u][1], pos[v][1], None]
	edge_trace = go.Scatter(x=edges_x, y=edges_y, mode='lines', line=dict(width=2,color='#5aa9ff'))
	node_trace = go.Scatter(x=x,y=y,mode='markers+text',text=text, textposition='top center', marker=dict(size=14,color='#1f9bd1'))
	fig = go.Figure(data=[edge_trace, node_trace])
	fig.update_layout(showlegend=False, template='plotly_dark', margin=dict(l=0,r=0,t=20,b=0))
	return fig


# Base CSS (light mode default, paddings, button glow)
st.markdown(
	"""
	<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
	<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
	<link href=\"https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800;900&display=swap\" rel=\"stylesheet\">
	<style>
	  :root { --glow: #5aa9ff; }
	  html, body { font-size: 18px; }
	  .block-container { padding: 18px 24px 24px 24px !important; }
	  .ocean-card { background: radial-gradient(1200px 400px at 10% 10%, rgba(90,169,255,0.08), rgba(255,255,255,0.02)); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 14px; }
	  h1, .stMarkdown h1 { font-size: 48px; font-weight: 900; }
	  h2, .stMarkdown h2 { font-size: 34px; font-weight: 800; }
	  h3, .stMarkdown h3 { font-size: 26px; font-weight: 700; }
	  .mtx-brand { font-weight: 900; font-size: 26px; white-space: nowrap; display: inline-block; margin-right: 24px; }
	  .mtx-nav { padding-top: 6px; margin-left: 12px; }
	  .mtx-nav a { color: #c7c9d1; margin-right: 16px; text-decoration: none; font-size: 16px; }
	  .mtx-hero { padding-top: 2vh; text-align: center; }
	  .mtx-logo { font-size: 72px; font-weight: 950; letter-spacing: -1px; }
	  .mtx-sub { font-size: 20px; color: #c7c9d1; }
	  .mtx-search { max-width: 900px; margin: 8px auto; }
	  .mtx-footer { padding: 10px; color: #9aa0a6; border-top: 1px solid rgba(255,255,255,0.06); text-align: center; margin-top: 3vh; }
	  .stTextInput>div>div>input { height: 48px; font-size: 18px; }
	  .glow-btn button { position: relative; border-radius: 999px; overflow: hidden; background: rgba(90,169,255,0.08); color: #e6e7eb; border: 1px solid transparent; }
	  .glow-btn button::before { content: ""; position: absolute; inset: -2px; padding: 2px; border-radius: 999px; background: conic-gradient(from 0deg, #5aa9ff, #7ce8ff, #5aa9ff 70%); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; animation: spinGlow 2.2s linear infinite; }
	  @keyframes spinGlow { to { transform: rotate(360deg); } }
	</style>
	""",
	unsafe_allow_html=True,
)


# Add padding to bring the header lower
st.markdown(
    """
    <style>
        .block-container { padding-top: 40px !important; } /* Adjust padding as needed */
    </style>
    """,
    unsafe_allow_html=True,
)


# Header + Nav (Deep-Sea Focus)
header_cols = st.columns([3, 6, 3])
with header_cols[0]:
	st.markdown("<div class='mtx-brand'>🌊 MarineTaxa<span style='color:#5aa9ff'>.ai</span></div>", unsafe_allow_html=True)
with header_cols[1]:
	st.markdown("<div style='text-align: center; color: #7ce8ff; font-size: 16px; margin-top: 8px;'>AI-Driven Deep-Sea eDNA Biodiversity System for Novel Taxa Discovery</div>", unsafe_allow_html=True)
with header_cols[2]:
	st.markdown("<div class='glow-btn'>", unsafe_allow_html=True)
	# Show the mode we will switch TO, not the current mode
	mode_btn = st.button("Research Mode" if st.session_state["mode"] == "user" else "Field Mode", key="mode_btn")
	st.markdown("</div>", unsafe_allow_html=True)
if mode_btn:
	st.session_state["mode"] = "research" if st.session_state["mode"] == "user" else "user"
	st.rerun()


# Inject dynamic backgrounds per mode (full app container)
if st.session_state["mode"] == "research":
	st.markdown(
		"""
		<style>
		[data-testid="stAppViewContainer"], .stApp { background: linear-gradient(180deg,#050a13 0%, #08111c 50%, #081320 100%) !important; }
		</style>
		""",
		unsafe_allow_html=True,
	)
else:
	st.markdown(
		"""
		<style>
		[data-testid="stAppViewContainer"], .stApp { background: linear-gradient(180deg,#0d2b4a 0%, #114b77 50%, #0d3254 100%) !important; }
		</style>
		""",
		unsafe_allow_html=True,
	)


# Hero with centered search bar
st.markdown("<div class='mtx-hero'><div class='mtx-logo'>MarineTaxa.ai</div><div class='mtx-sub'>The AI-Powered Portal for Marine Biodiversity Discovery</div></div>", unsafe_allow_html=True)

with st.container():
	st.markdown("<div class='mtx-search ocean-card'>", unsafe_allow_html=True)
	with st.form("search_form", clear_on_submit=False):
		seq = st.text_input(
			"Paste DNA/eDNA sequence",
			value=st.session_state["single_sequence"],
			placeholder="Paste DNA/eDNA sequence (ATCG only) and press Analyze",
			label_visibility="collapsed",
		)
		submitted = st.form_submit_button("Analyze", type="primary")
		st.session_state["single_sequence"] = seq
		if submitted:
			st.session_state["analysis_trigger"] = True
	st.markdown("</div>", unsafe_allow_html=True)


# Tabs (Deep-Sea eDNA Focus)
_tab_overview, _tab_novel_taxa, _tab_deep_sea_map, _tab_ai_pipeline, _tab_database, _tab_expert_review, _tab_research = st.tabs(["Deep-Sea Analysis", "Novel Taxa Discovery", "Bathymetry Explorer", "AI Pipeline", "Deep-Sea Database", "Expert Review", "Research Hub"])


with _tab_overview:
	st.markdown("# Deep-Sea eDNA Analysis Dashboard")
	st.markdown("*AI-powered novel taxa discovery in data-scarce deep-sea environments*")
	
	# Deep-Sea Sample Metadata Input
	st.markdown("## Deep-Sea Sample Context")
	metadata_cols = st.columns(4)
	with metadata_cols[0]:
		depth = st.number_input("Depth (m)", min_value=200, max_value=11000, value=2000)
		pressure = st.number_input("Pressure (bar)", min_value=20, max_value=1100, value=200)
	with metadata_cols[1]:
		temperature = st.number_input("Temperature (°C)", min_value=-2.0, max_value=25.0, value=2.0)
		salinity = st.number_input("Salinity (PSU)", min_value=30.0, max_value=40.0, value=34.7)
	with metadata_cols[2]:
		oxygen = st.number_input("Oxygen (mg/L)", min_value=0.0, max_value=10.0, value=3.5)
		cruise_id = st.text_input("Cruise ID", value="DS2025-001")
	with metadata_cols[3]:
		seamount_name = st.text_input("Location", value="Mariana Trench")
		station_replicate = st.text_input("Station", value="ST-047-R1")
	
	# Results by mode - Deep-Sea Focus
	if st.session_state["analysis_trigger"] and st.session_state["single_sequence"].strip():
		st.markdown("---")
		if st.session_state["mode"] == "user":
			st.subheader("Deep-Sea Sequence Analysis (Field Mode)")
			meta_cols = st.columns(5)
			meta_cols[0].metric("Novelty Score", "0.87", "High novelty detected")
			meta_cols[1].metric("Cluster ID", "DeepSea_C047", "Novel cluster")
			meta_cols[2].metric("Depth Context", f"{depth}m", "Abyssal zone" if depth > 4000 else "Bathyal zone")
			meta_cols[3].metric("Reference Distance", ">15%", "No close matches")
			meta_cols[4].metric("Candidate Status", "Novel Taxa", "Score >0.8 threshold")
			
			# AI-Driven Novelty Detection Display
			st.markdown("### AI-Driven Novelty Detection")
			novelty_cols = st.columns(3)
			with novelty_cols[0]:
				st.markdown("""
				**Autoencoder Reconstruction Error:** 0.87  
				**Embedding Distance:** 0.34  
				**K-mer Novelty:** 0.82  
				""")
			with novelty_cols[1]:
				st.markdown("""
				**Geographic Origin:** Mariana Trench  
				**Depth Category:** Abyssal (>4000m)  
				**Environmental Context:** High pressure, low temp  
				""")
			with novelty_cols[2]:
				st.markdown("""
				**Cluster Assignment:** Primary clustering complete  
				**Reference Lookup:** Optional (independent)  
				**Expert Review:** Queued for validation  
				""")
			
			st.info("**Taxonomy-Free Analysis:** This sequence shows high novelty and has been assigned to a new cluster without relying on reference databases.")
			
			# Taxonomy-Free Biodiversity Assessment
			st.markdown("### Taxonomy-Free Biodiversity Assessment")
			biodiv_cols = st.columns(4)
			with biodiv_cols[0]:
				st.metric("Cluster Richness", "47", "Unique clusters")
			with biodiv_cols[1]:
				st.metric("Shannon Index", "3.42", "Cluster diversity")
			with biodiv_cols[2]:
				st.metric("Simpson Index", "0.89", "Cluster evenness")
			with biodiv_cols[3]:
				st.metric("Rarefaction Slope", "0.73", "Discovery rate")
			
			st.markdown("**Novel Taxa Clustering Visualization**")
			st.plotly_chart(user_taxa_sunburst(), use_container_width=True)
		else:
			st.subheader("Deep-Sea Sequence Analysis (Research Mode)")
			meta_cols = st.columns(5)
			meta_cols[0].metric("Novelty Score", "0.87", "High novelty")
			meta_cols[1].metric("Cluster ID", "DeepSea_C047", "Novel cluster")
			meta_cols[2].metric("Embedding Distance", "0.34", "Distinct signature")
			meta_cols[3].metric("Reference Distance", ">15%", "No close matches")
			meta_cols[4].metric("Expert Review", "Pending", "Awaiting validation")
			
			st.write("**Deep-Sea Novelty Analysis**")
			novelty_df = pd.DataFrame({
				"Metric": ["Sequence Embedding", "K-mer Profile", "GC Content", "Length Distribution"],
				"Score": [0.87, 0.82, 0.91, 0.76],
				"Threshold": [0.7, 0.7, 0.8, 0.6],
				"Status": ["Novel", "Novel", "Novel", "Novel"]
			})
			st.dataframe(novelty_df, use_container_width=True)
			st.markdown("**Deep-Sea Cluster Network**")
			st.plotly_chart(research_network_graph(), use_container_width=True)
			st.download_button("Download Cluster Data", data=b"cluster_id,novelty_score,depth_context\nDeepSea_C047,0.87,abyssal", file_name="deep_sea_clusters.csv")
	else:
		st.caption("Enter a deep-sea eDNA sequence to analyze for novel taxa discovery.")

	# Deep-Sea Dashboard
	st.markdown("---\n### Deep-Sea eDNA Discovery Dashboard")
	dash_cols = st.columns([3, 2])
	with dash_cols[0]:
		# Deep-sea sampling locations with bathymetry context
		deep_sea_df = pd.DataFrame({
			"lat": [11.35, -15.0, 26.0, 47.0, -68.35],
			"lon": [142.2, 40.0, -105.0, 179.0, 77.58],
			"depth": [4990, 3200, 407, 2762, 1200],
			"novel_taxa": [12, 8, 47, 6, 15],
			"label": ["Mariana Trench", "Mozambique Deep", "Salas y Gómez Ridge", "Bounty Trough", "Antarctic Deep"],
		})
		fig_map = px.scatter_mapbox(
			deep_sea_df, 
			lat="lat", 
			lon="lon", 
			color="novel_taxa", 
			size="depth",
			hover_name="label", 
			hover_data={"depth": True, "novel_taxa": True},
			color_continuous_scale="Viridis", 
			zoom=1, 
			height=420,
			title="Deep-Sea Novel Taxa Discovery Sites"
		)
		fig_map.update_layout(mapbox_style="open-street-map", margin=dict(l=0,r=0,t=40,b=0))
		st.plotly_chart(fig_map, use_container_width=True)
	with dash_cols[1]:
		st.metric("Deep-Sea Samples", "847", "+23 this month")
		st.metric("Novel Taxa Candidates", "234", "+12 this week")
		st.metric("Depth Range", "200-11,000m", "Full bathyal-abyssal")
		st.metric("Clustering Precision", "80-90%", "Known taxa only")
		
		# Deep-Sea Validation Metrics
		st.markdown("**Deep-Sea Performance**")
		st.metric("Species Assignment", "60-75%", "Deep-sea accuracy")
		st.metric("Novelty Detection TPR", "70% (±5%)", "True positive rate")
		
		# Model Limitations Disclosure
		st.warning("""
		**Model Limitations:**
		- Deep-sea reference scarcity limits assignment confidence
		- ~40% of reads may be unmatched (novel candidates)
		- Performance varies with sample depth and environmental conditions
		""")

	# Upload/QC for large marine datasets
	st.markdown("---\n### Data Upload & Quality Check")
	st.info("**Large Dataset Support:** Upload files up to 5GB each. Supports FASTA, FASTQ, and compressed formats (.gz, .bz2)")
	
	up_cols = st.columns([2, 3])
	with up_cols[0]:
		uploaded = st.file_uploader(
			"Drag & drop or Browse", 
			type=["fa", "fasta", "fastq", "fq", "gz", "bz2", "zip"], 
			accept_multiple_files=True,
			help="Supports large marine eDNA datasets up to 5GB per file. Accepted formats: FASTA, FASTQ, and compressed files."
		)
		if uploaded:
			existing = {(f.name, getattr(f, "size", None)) for f in st.session_state["uploaded_files"]}
			for f in uploaded:
				key = (f.name, getattr(f, "size", None))
				if key not in existing:
					st.session_state["uploaded_files"].append(f)
		if st.session_state["uploaded_files"]:
			clear = st.button("Clear Files")
			if clear:
				st.session_state["uploaded_files"] = []
	with up_cols[1]:
		st.markdown("**Uploaded Files**")
		if st.session_state["uploaded_files"]:
			total_size = 0
			for f in st.session_state["uploaded_files"]:
				file_size = getattr(f, 'size', 0)
				total_size += file_size
				# Convert bytes to human-readable format
				if file_size < 1024:
					size_str = f"{file_size} B"
				elif file_size < 1024**2:
					size_str = f"{file_size/1024:.1f} KB"
				elif file_size < 1024**3:
					size_str = f"{file_size/(1024**2):.1f} MB"
				else:
					size_str = f"{file_size/(1024**3):.1f} GB"
				st.write(f"• {f.name}  ({size_str})")
			
			# Display total size
			if total_size < 1024**3:
				total_size_str = f"{total_size/(1024**2):.1f} MB"
			else:
				total_size_str = f"{total_size/(1024**3):.1f} GB"
			
			left, right = st.columns(2)
			with left:
				st.metric("Files", len(st.session_state["uploaded_files"]))
			with right:
				st.metric("Total Size", total_size_str)
		else:
			st.info("No files uploaded yet. Marine eDNA datasets can be large - we support up to 5GB per file!")

	# Placeholders and galleries (kept)
	st.markdown("---\n### Interactive Sample Reports: Coral Reef eDNA")
	st.image(make_placeholder("Sample report screenshot"))

	st.markdown("---\n### What researchers say")
	q1, q2 = st.columns(2)
	with q1:
		st.image(make_placeholder("Dr. Arun photo"))
		st.markdown("“MarineTaxa.ai saved me weeks of analysis for our expedition data.” – **Dr. Arun**, Ocean Researcher")
	with q2:
		st.image(make_placeholder("Priya photo"))
		st.markdown("“Uploading FASTQ files and getting annotated taxa in minutes is game-changing!” – **Priya**, MSc student")

	st.markdown("---\n### Dashboard & Explorer")
	st.image(make_placeholder("Dashboard mockup"))
	st.markdown("---\n### Methodology Explainer")
	st.image(make_placeholder("Pipeline diagram"))
	st.markdown("---\n### API Access & Advanced Tools")
	st.image(make_placeholder("API docs screenshot"))
	st.markdown("---\n### Learning Center")
	st.image(make_placeholder("Learning center"))

	st.markdown("---\n### Essential Advanced Visual Features")
	av1, av2 = st.columns(2)
	with av1:
		st.plotly_chart(px.pie(values=[40,25,20,15], names=["Fish","Corals","Crustaceans","Molluscs"], title="Composition by group"), use_container_width=True)
		st.plotly_chart(px.bar(x=["Shannon","Simpson"], y=[2.1,0.86], title="Diversity Indices"), use_container_width=True)
	with av2:
		st.image(make_placeholder("UMAP/Cluster plot"))
		st.image(make_placeholder("Network graph"))
	st.image(make_placeholder("Interactive taxa table & cluster stats"))
	st.image(make_placeholder("Geographic map of discoveries"))
	st.image(make_placeholder("Classical vs AI comparison"))

	st.markdown("---\n### Modes")
	st.image(make_placeholder("Modes infographic"))


with _tab_novel_taxa:
	st.markdown("# AI-Driven Novel Taxa Discovery")
	st.markdown("*Advanced novelty detection using autoencoder reconstruction error and taxonomy-free clustering*")
	
	# AI-Driven Novelty Detection Module
	st.markdown("## AI-Driven Novelty Detection Module")
	
	st.info("""
	**Autoencoder-Based Novelty Detection:**
	- Reconstruction error on DNABERT-2 sequence embeddings
	- Sequences with score >0.8 flagged as "Candidate Novel Taxa"
	- Independent of reference database availability
	- Validated on deep-sea expert-curated datasets
	""")
	
	# Novelty Detection Controls
	st.markdown("## Novelty Detection Parameters")
	
	novelty_cols = st.columns(4)
	with novelty_cols[0]:
		novelty_threshold = st.slider("Novelty Threshold", 0.0, 1.0, 0.8, 0.05, help="Sequences above this score are flagged as novel taxa candidates", key="novelty_threshold_detection")
	with novelty_cols[1]:
		cluster_method = st.selectbox("Clustering Method", ["HDBSCAN", "UMAP + HDBSCAN", "DBSCAN", "Gaussian Mixture"], key="cluster_method_novelty")
	with novelty_cols[2]:
		embedding_model = st.selectbox("Embedding Model", ["DNABERT-2", "Nucleotide Transformer", "ESM-2"], key="embedding_model_novelty")
	with novelty_cols[3]:
		min_cluster_size = st.number_input("Min Cluster Size", min_value=3, max_value=50, value=5, key="min_cluster_size_novelty")
	
	# Reference Database Independence Toggle
	st.markdown("## Reference Database Independence")
	
	independence_cols = st.columns(2)
	with independence_cols[0]:
		show_references = st.toggle("Show Reference Annotations", value=False, help="Toggle to hide/show database matches and focus on clusters")
		clustering_first = st.checkbox("Primary Clustering First", value=True, help="Perform sequence clustering before reference lookup")
	with independence_cols[1]:
		st.markdown("""
		**Processing Order:**
		1. Sequence embedding (DNABERT-2)
		2. Unsupervised clustering (HDBSCAN)
		3. Novelty scoring (Autoencoder)
		4. Reference annotation (Optional)
		""")
	
	# Novel Taxa Clusters
	st.markdown("## Novel Taxa Clusters")
	
	# Enhanced cluster data with geographic origin and novelty flagging
	cluster_data = pd.DataFrame({
		"Cluster_ID": [f"DeepSea_C{str(i).zfill(3)}" for i in range(1, 21)],
		"Sequences": [45, 23, 67, 12, 89, 34, 56, 78, 29, 91, 15, 43, 62, 38, 71, 26, 84, 19, 52, 37],
		"Novelty_Score": [0.92, 0.87, 0.94, 0.83, 0.96, 0.81, 0.89, 0.93, 0.85, 0.97, 0.79, 0.88, 0.91, 0.86, 0.95, 0.82, 0.90, 0.84, 0.87, 0.83],
		"Depth_Range": ["2000-4000m", "1000-2000m", "4000-6000m", "500-1000m", "6000-8000m", "1500-2500m", "3000-5000m", "4500-6500m", "800-1200m", "7000-9000m", "600-800m", "2500-3500m", "3500-4500m", "1800-2800m", "5000-7000m", "1200-1800m", "4000-5000m", "900-1100m", "2800-3800m", "1600-2200m"],
		"Geographic_Origin": ["Mariana Trench", "Mid-Atlantic Ridge", "Puerto Rico Trench", "Azores Plateau", "Japan Trench", "Canary Basin", "Kermadec Trench", "Peru-Chile Trench", "Iberian Margin", "Challenger Deep", "Rockall Trough", "Hatteras Plain", "Bermuda Rise", "Reykjanes Ridge", "Mendocino Fracture", "Cascadia Basin", "Aleutian Trench", "Tonga Trench", "Chile Rise", "Argentine Basin"],
		"Candidate_Novel": ["Yes", "Yes", "Yes", "No", "Yes", "No", "Yes", "Yes", "No", "Yes", "No", "Yes", "Yes", "No", "Yes", "No", "Yes", "No", "Yes", "No"],
		"Status": ["Novel", "Novel", "Novel", "Pending Review", "Novel", "Pending Review", "Novel", "Novel", "Pending Review", "Novel", "Known", "Novel", "Novel", "Pending Review", "Novel", "Known", "Novel", "Pending Review", "Novel", "Pending Review"]
	})
	
	# Flag sequences with score >0.8 as Candidate Novel Taxa
	cluster_data["Candidate_Novel"] = cluster_data["Novelty_Score"].apply(lambda x: "Yes" if x > novelty_threshold else "No")
	
	# Filter clusters by novelty threshold
	filtered_clusters = cluster_data[cluster_data["Novelty_Score"] >= novelty_threshold]
	
	st.dataframe(filtered_clusters, use_container_width=True)
	
	# Novelty Score Distribution
	st.markdown("## Novelty Score Distribution")
	
	fig_hist = px.histogram(
		cluster_data, 
		x="Novelty_Score", 
		nbins=20,
		title="Distribution of Novelty Scores Across Clusters",
		color_discrete_sequence=["#5aa9ff"]
	)
	fig_hist.add_vline(x=novelty_threshold, line_dash="dash", line_color="red", annotation_text="Threshold")
	fig_hist.update_layout(template="plotly_dark")
	st.plotly_chart(fig_hist, use_container_width=True)
	
	# Cluster Visualization
	st.markdown("## Cluster Embedding Visualization")
	
	# Simulated 2D embedding data
	import numpy as np
	np.random.seed(42)
	n_points = 200
	embedding_data = pd.DataFrame({
		"x": np.random.randn(n_points),
		"y": np.random.randn(n_points),
		"cluster": np.random.choice(filtered_clusters["Cluster_ID"].tolist(), n_points),
		"novelty": np.random.uniform(0.7, 1.0, n_points)
	})
	
	fig_scatter = px.scatter(
		embedding_data,
		x="x",
		y="y",
		color="cluster",
		size="novelty",
		hover_data=["novelty"],
		title="Deep-Sea eDNA Sequence Clustering (2D Projection)",
		template="plotly_dark"
	)
	st.plotly_chart(fig_scatter, use_container_width=True)
	
	# Export Options
	st.markdown("## Export Novel Taxa Data")
	
	export_cols = st.columns(3)
	with export_cols[0]:
		if st.button("Export Cluster Data", use_container_width=True):
			st.info("Downloading novel taxa cluster data...")
	with export_cols[1]:
		if st.button("Export Sequences", use_container_width=True):
			st.info("Downloading representative sequences...")
	with export_cols[2]:
		if st.button("Generate Report", use_container_width=True):
			st.info("Generating novel taxa discovery report...")

# Removed old _tab_marine section - functionality integrated into new tab structure


with _tab_deep_sea_map:
	st.markdown("# Deep-Sea Bathymetry Explorer")
	st.markdown("*Interactive deep-sea sampling visualization with ocean floor topography*")
	
	# Depth Controls
	st.markdown("## Depth Filtering Controls")
	
	depth_cols = st.columns(4)
	with depth_cols[0]:
		min_depth = st.slider("Minimum Depth (m)", 0, 11000, 200, 100)
	with depth_cols[1]:
		max_depth = st.slider("Maximum Depth (m)", 0, 11000, 6000, 100)
	with depth_cols[2]:
		show_trenches = st.checkbox("Show Ocean Trenches", value=True)
	with depth_cols[3]:
		show_ridges = st.checkbox("Show Mid-Ocean Ridges", value=True)
	
	# Deep-Sea Features Toggle
	feature_cols = st.columns(3)
	with feature_cols[0]:
		show_seamounts = st.checkbox("Seamounts", value=True)
	with feature_cols[1]:
		show_abyssal_plains = st.checkbox("Abyssal Plains", value=True)
	with feature_cols[2]:
		show_hydrothermal_vents = st.checkbox("Hydrothermal Vents", value=True)
	
	# Bathymetric Map with Deep-Sea Sampling Sites
	st.markdown("## Deep-Sea Sampling Network")
	
	# Enhanced deep-sea sampling data with bathymetric context
	bathymetric_data = pd.DataFrame({
		"lat": [11.35, -15.0, -22.0, 26.0, 47.0, -68.35, 36.7, -50.5, 14.2, -37.8],
		"lon": [142.2, 40.0, 166.0, -105.0, 179.0, 77.58, -3.0, 70.0, -17.8, 77.5],
		"depth": [4990, 3200, 2100, 407, 2762, 1200, 3800, 4200, 3500, 2900],
		"novel_taxa": [12, 8, 15, 47, 6, 15, 9, 11, 7, 13],
		"feature_type": ["Trench", "Abyssal Plain", "Seamount", "Ridge", "Trench", "Continental Slope", "Abyssal Plain", "Ridge", "Seamount", "Abyssal Plain"],
		"location": ["Mariana Trench", "Mozambique Deep", "New Caledonia Seamount", "Salas y Gómez Ridge", "Bounty Trough", "Antarctic Slope", "Iberian Abyssal Plain", "Southwest Indian Ridge", "Canary Seamount", "Crozet Basin"],
		"temperature": [1.8, 2.1, 3.2, 4.5, 1.9, 0.8, 2.3, 2.7, 3.8, 2.0],
		"pressure": [499, 320, 210, 41, 276, 120, 380, 420, 350, 290]
	})
	
	# Filter by depth range
	filtered_data = bathymetric_data[
		(bathymetric_data["depth"] >= min_depth) & 
		(bathymetric_data["depth"] <= max_depth)
	]
	
	# Create bathymetric visualization
	fig_bathy = px.scatter_mapbox(
		filtered_data,
		lat="lat",
		lon="lon",
		color="depth",
		size="novel_taxa",
		hover_name="location",
		hover_data={
			"feature_type": True,
			"depth": True,
			"novel_taxa": True,
			"temperature": True,
			"pressure": True
		},
		color_continuous_scale="Viridis_r",  # Reversed for depth (darker = deeper)
		size_max=25,
		zoom=1,
		height=600,
		title="Deep-Sea eDNA Sampling Sites with Bathymetric Context"
	)
	
	fig_bathy.update_layout(
		mapbox_style="open-street-map",
		margin=dict(l=0,r=0,t=40,b=0),
		template="plotly_dark"
	)
	
	st.plotly_chart(fig_bathy, use_container_width=True)
	
	# Depth Profile Analysis
	st.markdown("## Depth Profile Analysis")
	
	profile_cols = st.columns(2)
	with profile_cols[0]:
		# Novel taxa by depth
		fig_depth = px.scatter(
			filtered_data,
			x="depth",
			y="novel_taxa",
			color="feature_type",
			size="temperature",
			hover_name="location",
			title="Novel Taxa Discovery vs Depth",
			labels={"depth": "Depth (m)", "novel_taxa": "Novel Taxa Count"}
		)
		fig_depth.update_layout(template="plotly_dark")
		st.plotly_chart(fig_depth, use_container_width=True)
		
	with profile_cols[1]:
		# Temperature-Pressure relationship
		fig_temp_press = px.scatter(
			filtered_data,
			x="temperature",
			y="pressure",
			color="novel_taxa",
			size="depth",
			hover_name="location",
			title="Temperature-Pressure Relationship",
			labels={"temperature": "Temperature (°C)", "pressure": "Pressure (bar)"}
		)
		fig_temp_press.update_layout(template="plotly_dark")
		st.plotly_chart(fig_temp_press, use_container_width=True)
	
	# Deep-Sea Feature Statistics
	st.markdown("## Deep-Sea Feature Analysis")
	
	feature_stats = filtered_data.groupby("feature_type").agg({
		"novel_taxa": ["sum", "mean"],
		"depth": ["mean", "min", "max"],
		"location": "count"
	}).round(2)
	
	st.dataframe(feature_stats, use_container_width=True)
	
	# Sampling Recommendations
	st.markdown("## AI-Powered Sampling Recommendations")
	
	st.info("""
	**High Priority Sampling Areas (Based on Novelty Prediction Model):**
	
	1. **Puerto Rico Trench** (19.7°N, 67.5°W) - Predicted novelty score: 0.91
	2. **Japan Trench** (39.5°N, 143.9°E) - Predicted novelty score: 0.89  
	3. **Peru-Chile Trench** (23.0°S, 71.0°W) - Predicted novelty score: 0.87
	4. **Kermadec Trench** (30.0°S, 177.0°W) - Predicted novelty score: 0.85
	
	*Recommendations based on depth, isolation, and environmental uniqueness factors.*
	""")
	
	# Export Bathymetric Data
	export_bathy_cols = st.columns(3)
	with export_bathy_cols[0]:
		if st.button("Export Sampling Data", key="export_sampling"):
			st.info("Downloading bathymetric sampling data...")
	with export_bathy_cols[1]:
		if st.button("Generate Depth Report", key="export_depth"):
			st.info("Generating depth profile analysis...")
	with export_bathy_cols[2]:
		if st.button("Download Coordinates", key="export_coords"):
			st.info("Downloading GPS coordinates for field work...")

with _tab_ai_pipeline:
	st.markdown("# AI Pipeline for Deep-Sea eDNA")
	st.markdown("*Taxonomy-free processing workflow for novel taxa discovery*")
	
	# Pipeline Overview
	st.markdown("## Processing Pipeline Overview")
	
	pipeline_steps = [
		"1. Raw Sequence Input",
		"2. Quality Filtering",
		"3. DNA Embedding (DNABERT)",
		"4. Taxonomy-Free Clustering",
		"5. Novelty Detection",
		"6. Expert Review Queue",
		"7. Reference Annotation (Optional)"
	]
	
	pipeline_cols = st.columns(len(pipeline_steps))
	for i, (col, step) in enumerate(zip(pipeline_cols, pipeline_steps)):
		with col:
			if i < 3:
				st.success(f"Complete: {step}")
			elif i < 5:
				st.warning(f"Processing: {step}")
			else:
				st.info(f"Pending: {step}")
	
	# GPU-Optimized Genomic Processing
	st.markdown("## GPU-Optimized Genomic Processing")
	
	gpu_cols = st.columns(3)
	with gpu_cols[0]:
		st.markdown("""
		### CUDA-Enabled Processing
		- **DNABERT-2 Inference:** GPU-accelerated
		- **Embedding Computation:** Parallel processing
		- **Clustering Operations:** GPU-optimized HDBSCAN
		- **Autoencoder Scoring:** Batch processing
		""")
	with gpu_cols[1]:
		st.markdown("""
		### Hardware Benchmarks
		- **NVIDIA V100:** 500 sequences/min
		- **NVIDIA A100:** 1,000 sequences/min
		- **CPU Fallback:** 100 sequences/min
		- **Memory Usage:** 8-16GB GPU RAM
		""")
	with gpu_cols[2]:
		st.markdown("""
		### Compute Resources
		- **GPU Utilization:** Real-time monitoring
		- **Throughput Metrics:** Live performance tracking
		- **Resource Requirements:** Hardware specifications
		- **Scaling Options:** Multi-GPU support planned
		""")
	
	# Real-time Processing Status
	st.markdown("## Real-Time Processing Status")
	
	status_cols = st.columns(4)
	with status_cols[0]:
		st.metric("Sequences in Queue", "1,247", "+89 in last hour")
	with status_cols[1]:
		st.metric("GPU Processing Rate", "~500/min", "NVIDIA V100")
	with status_cols[2]:
		st.metric("A100 Processing Rate", "~1000/min", "Next-gen GPU")
	with status_cols[3]:
		st.metric("Avg Sample Time", "20 min", "10K reads + V100")
	
	# Processing Time Disclaimer
	st.info("""
	**GPU-Optimized Processing:**
	- CUDA-enabled DNABERT inference for embedding computation
	- GPU-accelerated clustering with parallel HDBSCAN
	- Batch autoencoder processing for novelty detection
	- Real-time GPU utilization and throughput monitoring
	""")
	
	# Processing Performance Comparison
	st.markdown("## Processing Performance: CPU vs GPU")
	
	# Realistic Performance data for deep-sea eDNA
	performance_data = pd.DataFrame({
		"Method": ["Traditional BLAST", "CPU Clustering", "GPU + DNABERT", "Our AI Pipeline"],
		"Sequences_per_minute": [12, 45, 320, 500],
		"Deep_Sea_Accuracy": [0.45, 0.52, 0.68, 0.72],
		"Reference_Dependence": ["High", "High", "Medium", "Low"],
		"Novel_Taxa_Detection": [0.15, 0.23, 0.58, 0.70]
	})
	
	perf_cols = st.columns(2)
	with perf_cols[0]:
		fig_speed = px.bar(
			performance_data,
			x="Method",
			y="Sequences_per_minute",
			title="Processing Speed Comparison",
			color="Sequences_per_minute",
			color_continuous_scale="Viridis"
		)
		fig_speed.update_layout(template="plotly_dark")
		st.plotly_chart(fig_speed, use_container_width=True)
		
	with perf_cols[1]:
		fig_accuracy = px.bar(
			performance_data,
			x="Method",
			y="Deep_Sea_Accuracy",
			title="Deep-Sea Species Assignment Accuracy",
			color="Deep_Sea_Accuracy",
			color_continuous_scale="Plasma"
		)
		fig_accuracy.update_layout(template="plotly_dark")
		st.plotly_chart(fig_accuracy, use_container_width=True)
	
	# Deep-Sea Specific Validation Metrics
	st.markdown("## Deep-Sea Specific Validation Metrics")
	
	validation_cols = st.columns(4)
	with validation_cols[0]:
		st.metric("Deep-Sea Recall", "72%", "Known deep-sea species correctly clustered")
	with validation_cols[1]:
		st.metric("Global Recall", "85%", "All marine species (shallow + deep)")
	with validation_cols[2]:
		st.metric("Deep-Sea Novelty FDR", "28%", "False discovery rate by depth")
	with validation_cols[3]:
		st.metric("Trench Validation", "68%", "Hadal zone performance")
	
	# Validation by Depth Category
	st.markdown("### Performance by Depth Category")
	
	depth_performance = pd.DataFrame({
		"Depth_Category": ["Bathyal (200-4000m)", "Abyssal (4000-6000m)", "Hadal (>6000m)", "Trenches", "Seamounts", "Abyssal Plains"],
		"Deep_Sea_Recall": [0.78, 0.72, 0.68, 0.65, 0.74, 0.71],
		"Novelty_FDR": [0.22, 0.28, 0.32, 0.35, 0.26, 0.29],
		"Sample_Count": [245, 189, 67, 34, 156, 203]
	})
	
	depth_perf_cols = st.columns(2)
	with depth_perf_cols[0]:
		fig_recall = px.bar(
			depth_performance,
			x="Depth_Category",
			y="Deep_Sea_Recall",
			title="Deep-Sea Recall by Depth Category",
			color="Deep_Sea_Recall",
			color_continuous_scale="Blues"
		)
		fig_recall.update_layout(template="plotly_dark", xaxis_tickangle=-45)
		st.plotly_chart(fig_recall, use_container_width=True)
		
	with depth_perf_cols[1]:
		fig_fdr = px.bar(
			depth_performance,
			x="Depth_Category",
			y="Novelty_FDR",
			title="False Discovery Rate by Depth Category",
			color="Novelty_FDR",
			color_continuous_scale="Reds"
		)
		fig_fdr.update_layout(template="plotly_dark", xaxis_tickangle=-45)
		st.plotly_chart(fig_fdr, use_container_width=True)
	
	# Expert-Curated Test Sets
	st.markdown("### Expert-Curated Validation Sets")
	
	test_sets_cols = st.columns(3)
	with test_sets_cols[0]:
		st.markdown("""
		**Trench Validation Set**
		- 67 samples from major ocean trenches
		- Expert-identified species from morphology
		- Mariana, Puerto Rico, Japan trenches
		- Validation accuracy: 68%
		""")
	with test_sets_cols[1]:
		st.markdown("""
		**Seamount Validation Set**
		- 156 samples from seamount ecosystems
		- Endemic species focus
		- Mid-Atlantic Ridge, Emperor Seamounts
		- Validation accuracy: 74%
		""")
	with test_sets_cols[2]:
		st.markdown("""
		**Abyssal Plains Set**
		- 203 samples from abyssal plains
		- Sediment-dwelling fauna
		- Atlantic, Pacific basins
		- Validation accuracy: 71%
		""")
	
	# Performance Limitations
	st.warning("""
	**Deep-Sea Validation Challenges:**
	- Expert-curated test sets from trenches, seamounts, and abyssal plains
	- Performance degrades with increasing depth (Hadal < Abyssal < Bathyal)
	- Environmental extremes affect DNA quality and species detection
	- Limited morphological validation data for novel deep-sea taxa
	- Conservative bias in expert validation of novel species claims
	""")
	
	# AI Model Configuration
	st.markdown("## AI Model Configuration")
	
	model_cols = st.columns(3)
	with model_cols[0]:
		st.markdown("""
		### DNABERT Embedding
		- **Model:** DNABERT-2 (6-mer)
		- **Fine-tuning:** Deep-sea specific
		- **Embedding Dim:** 768
		- **Context Length:** 512 bp
		- **Training Data:** 2.4M deep-sea sequences
		""")
		
	with model_cols[1]:
		st.markdown("""
		### Clustering Algorithm
		- **Method:** HDBSCAN
		- **Min Cluster Size:** 5 sequences
		- **Distance Metric:** Cosine similarity
		- **Noise Handling:** Automatic outlier detection
		- **Hierarchy:** Multi-level clustering
		""")
		
	with model_cols[2]:
		st.markdown("""
		### Novelty Detection
		- **Approach:** Autoencoder reconstruction
		- **Threshold:** Adaptive (depth-dependent)
		- **Features:** Sequence + environmental
		- **Validation:** Expert feedback loop
		- **Confidence:** Bayesian uncertainty
		""")
	
	# Resource Usage Monitor
	st.markdown("## Resource Usage Monitor")
	
	# Simulated resource data
	import datetime
	import numpy as np
	
	time_points = [datetime.datetime.now() - datetime.timedelta(minutes=x) for x in range(60, 0, -5)]
	resource_data = pd.DataFrame({
		"timestamp": time_points,
		"gpu_usage": np.random.uniform(70, 95, len(time_points)),
		"memory_usage": np.random.uniform(60, 85, len(time_points)),
		"throughput": np.random.uniform(800, 900, len(time_points))
	})
	
	resource_cols = st.columns(2)
	with resource_cols[0]:
		fig_gpu = px.line(
			resource_data,
			x="timestamp",
			y="gpu_usage",
			title="GPU Utilization Over Time",
			labels={"gpu_usage": "GPU Usage (%)", "timestamp": "Time"}
		)
		fig_gpu.update_layout(template="plotly_dark")
		st.plotly_chart(fig_gpu, use_container_width=True)
		
	with resource_cols[1]:
		fig_throughput = px.line(
			resource_data,
			x="timestamp",
			y="throughput",
			title="Processing Throughput",
			labels={"throughput": "Sequences/min", "timestamp": "Time"}
		)
		fig_throughput.update_layout(template="plotly_dark")
		st.plotly_chart(fig_throughput, use_container_width=True)
	
	# Pipeline Configuration
	st.markdown("## Pipeline Configuration")
	
	config_cols = st.columns(4)
	with config_cols[0]:
		batch_size = st.selectbox("Batch Size", [32, 64, 128, 256], index=2)
	with config_cols[1]:
		embedding_model = st.selectbox("Embedding Model", ["DNABERT-2", "Nucleotide Transformer", "ESM-2"], key="embedding_model_pipeline")
	with config_cols[2]:
		clustering_method = st.selectbox("Clustering", ["HDBSCAN", "DBSCAN", "Gaussian Mixture"], key="clustering_method_pipeline")
	with config_cols[3]:
		novelty_threshold = st.slider("Novelty Threshold", 0.5, 0.95, 0.7, key="novelty_threshold_pipeline")
	
	# Advanced Settings
	with st.expander("Advanced Pipeline Settings"):
		adv_cols = st.columns(3)
		with adv_cols[0]:
			st.number_input("Min Sequence Length", min_value=50, max_value=1000, value=150, key="min_seq_length")
			st.number_input("Max Sequence Length", min_value=500, max_value=5000, value=1500, key="max_seq_length")
		with adv_cols[1]:
			st.selectbox("Quality Filter", ["Phred > 20", "Phred > 25", "Phred > 30"], key="quality_filter")
			st.checkbox("Remove Chimeras", value=True, key="remove_chimeras")
		with adv_cols[2]:
			st.selectbox("Embedding Aggregation", ["Mean", "Max", "Attention"], key="embedding_aggregation")
			st.checkbox("Use Environmental Features", value=True, key="use_env_features")
	
	# Start Processing
	st.markdown("## Start Processing")
	
	process_cols = st.columns(3)
	with process_cols[0]:
		if st.button("Start Batch Processing", use_container_width=True):
			st.success("Processing started! Monitor progress above.")
	with process_cols[1]:
		if st.button("Pause Processing", use_container_width=True):
			st.warning("Processing paused.")
	with process_cols[2]:
		if st.button("Export Results", use_container_width=True):
			st.info("Exporting processed results...")

# Additional Database Content
with st.expander("Taxonomic Classification System", expanded=False):
	st.markdown("# Marine Taxonomic Classification & Reference Database")
	st.markdown("*Scientific classification, reference databases, and taxonomic relationships*")
	
	# Map 2: Taxonomic database coverage
	st.markdown("## Database Coverage Map")
	
	# Database coverage data
	coverage_data = pd.DataFrame({
		"lat": [0.0, 30.0, -30.0, 60.0, -60.0, 45.0, -45.0],
		"lon": [0.0, 0.0, 0.0, 0.0, 0.0, 180.0, 180.0],
		"region": ["Equatorial", "Northern Temperate", "Southern Temperate", "Arctic", "Antarctic", "North Pacific", "South Pacific"],
		"silva_coverage": [85, 92, 78, 65, 45, 88, 72],
		"unite_coverage": [72, 89, 68, 52, 38, 85, 65],
		"ncbi_sequences": [45000, 67000, 38000, 23000, 12000, 78000, 41000],
		"worms_species": [12000, 18000, 9500, 5600, 3200, 22000, 11000],
		"completeness": [78, 89, 73, 58, 41, 86, 69]
	})
	
	fig_coverage = px.scatter_mapbox(
		coverage_data,
		lat="lat",
		lon="lon",
		size="completeness",
		color="silva_coverage",
		hover_name="region",
		hover_data={"silva_coverage": True, "unite_coverage": True, "ncbi_sequences": True},
		color_continuous_scale="Viridis",
		size_max=25,
		zoom=1,
		height=500,
		title="Reference Database Coverage by Region"
	)
	fig_coverage.update_layout(
		mapbox_style="open-street-map",
		margin=dict(l=0,r=0,t=40,b=0),
		template="plotly_dark"
	)
	st.plotly_chart(fig_coverage, use_container_width=True)
	
	# Taxonomic hierarchy browser
	st.markdown("## Taxonomic Hierarchy Browser")
	
	hierarchy_cols = st.columns(4)
	with hierarchy_cols[0]:
		kingdom = st.selectbox("Kingdom", ["Animalia", "Plantae", "Fungi", "Protista", "Bacteria"])
	with hierarchy_cols[1]:
		phylum = st.selectbox("Phylum", ["Chordata", "Mollusca", "Arthropoda", "Cnidaria", "Porifera"])
	with hierarchy_cols[2]:
		class_sel = st.selectbox("Class", ["Actinopterygii", "Gastropoda", "Malacostraca", "Anthozoa", "Demospongiae"])
	with hierarchy_cols[3]:
		order = st.selectbox("Order", ["Perciformes", "Neogastropoda", "Decapoda", "Scleractinia", "Haplosclerida"])
	
	# Database statistics
	st.markdown("## Reference Database Statistics")
	
	db_stats_cols = st.columns(4)
	with db_stats_cols[0]:
		st.metric("SILVA Sequences", "2.4M", "Marine 16S/18S")
	with db_stats_cols[1]:
		st.metric("UNITE Records", "847K", "Marine fungi")
	with db_stats_cols[2]:
		st.metric("WoRMS Species", "240K", "Taxonomic authority")
	with db_stats_cols[3]:
		st.metric("NCBI GenBank", "5.7M", "Marine sequences")
	
	# Knowledge gaps analysis
	st.markdown("## Taxonomic Knowledge Gaps")
	
	gaps_cols = st.columns(2)
	with gaps_cols[0]:
		st.markdown("""
		### High Priority Sampling Regions
		
		**Deep-sea Environments (>1000m)**
		- Coverage: 30% of known diversity
		- Priority: Abyssal plains, seamounts, trenches
		- Estimated unknown species: 500,000+
		
		**Polar Regions**
		- Arctic coverage: 45%
		- Antarctic coverage: 38%
		- Endemic species potential: High
		
		**Tropical Seamounts**
		- Sampling coverage: 15%
		- Endemism rate: 60-80%
		- Priority locations: Pacific, Indian Ocean
		""")
		
	with gaps_cols[1]:
		st.markdown("""
		### Taxonomic Groups Needing Attention
		
		**Meiofauna**
		- Described species: <10% of estimated diversity
		- Size range: 0.1-1mm
		- Habitat: Sediments, biofilms
		
		**Deep-sea Microbes**
		- Culturable fraction: <1%
		- Functional diversity: Largely unknown
		- Biotechnology potential: High
		
		**Cryptic Species Complexes**
		- Morphologically identical species
		- Genetic divergence: Significant
		- Distribution: Global, all habitats
		""")
	
	# Phylogenetic diversity centers
	st.markdown("## Phylogenetic Diversity Centers")
	
	diversity_data = pd.DataFrame({
		"lat": [0.38, -22.0, 25.0, -35.0, 65.0],
		"lon": [130.52, 166.0, -80.0, 138.0, -18.0],
		"center": ["Coral Triangle", "New Caledonia", "Caribbean", "Southern Australia", "North Atlantic"],
		"endemic_species": [2500, 1200, 800, 1500, 600],
		"phylogenetic_diversity": [95, 88, 78, 85, 72],
		"evolutionary_significance": [98, 92, 85, 89, 75]
	})
	
	fig_diversity = px.scatter_mapbox(
		diversity_data,
		lat="lat",
		lon="lon",
		size="endemic_species",
		color="phylogenetic_diversity",
		hover_name="center",
		hover_data={"endemic_species": True, "evolutionary_significance": True},
		color_continuous_scale="Plasma",
		size_max=20,
		zoom=1,
		height=400
	)
	fig_diversity.update_layout(
		mapbox_style="open-street-map",
		margin=dict(l=0,r=0,t=0,b=0),
		template="plotly_dark"
	)
	st.plotly_chart(fig_diversity, use_container_width=True)

with _tab_database:
	st.markdown("# MarineTaxaAI Database")
	st.markdown("*Comprehensive marine eDNA datasets, reference databases, and research resources*")
	
	# Search and filter interface
	st.markdown("## Search & Filter Datasets")
	
	search_cols = st.columns(4)
	with search_cols[0]:
		gene_marker = st.selectbox("Gene Marker", ["All", "COI", "16S", "18S", "12S", "MiFish", "ITS"])
	with search_cols[1]:
		region_filter = st.selectbox("Region", ["All", "Arctic", "Pacific", "Atlantic", "Southern Ocean", "Mediterranean"])
	with search_cols[2]:
		year_filter = st.selectbox("Year", ["All", "2025", "2024", "2023", "2022", "2021"])
	with search_cols[3]:
		habitat_filter = st.selectbox("Habitat", ["All", "Coastal", "Deep-sea", "Polar", "Tropical", "Temperate"])
	
	# Featured Datasets Section
	st.markdown("## Featured Datasets")
	
	# Dataset 1: Arctic Svalbard
	st.markdown("""
	<div style="border: 1px solid rgba(90,169,255,0.3); border-radius: 8px; padding: 20px; margin: 16px 0; background: rgba(90,169,255,0.05);">
		<h3 style="color: #5aa9ff; margin-bottom: 12px;">Arctic Svalbard Metabarcoding (PRJNA1306041)</h3>
		<p><strong>Description:</strong> Biodiversity survey in Kongsfjorden, Svalbard during Polar Night</p>
		<p><strong>Gene Markers:</strong> COI & 18S | <strong>Sample Types:</strong> Seawater & Sediment</p>
		<div style="display: flex; gap: 20px; margin: 12px 0;">
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">204 SRA Experiments</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">205 BioSamples</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">9 Gbases</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">2.94 GB Total</span>
		</div>
		<p><strong>Institution:</strong> Alfred Wegener Institute | <strong>Registered:</strong> August 2025</p>
	</div>
	""", unsafe_allow_html=True)
	
	dataset_cols = st.columns(3)
	with dataset_cols[0]:
		if st.button("View Full Dataset", key="arctic_view"):
			st.info("Redirecting to PRJNA1306041 dataset details...")
	with dataset_cols[1]:
		if st.button("Download Metadata", key="arctic_meta"):
			st.info("Downloading Arctic Svalbard metadata CSV...")
	with dataset_cols[2]:
		if st.button("Access SRA", key="arctic_sra"):
			st.info("Opening SRA Toolkit access...")
	
	# Dataset 2: New Zealand Marine
	st.markdown("""
	<div style="border: 1px solid rgba(90,169,255,0.3); border-radius: 8px; padding: 20px; margin: 16px 0; background: rgba(90,169,255,0.05);">
		<h3 style="color: #5aa9ff; margin-bottom: 12px;">New Zealand Marine Monitoring & Biosecurity (PRJNA1332291)</h3>
		<p><strong>Description:</strong> Automated eDNA sampling across New Zealand coasts</p>
		<p><strong>Study Type:</strong> Multispecies, high-resolution, time-series monitoring</p>
		<div style="display: flex; gap: 20px; margin: 12px 0;">
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">59 SRA Experiments</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">31 Sample Sites</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">Time-series Data</span>
		</div>
		<p><strong>Funding:</strong> EU/Horizon & NZ MBIE Marine Grants</p>
	</div>
	""", unsafe_allow_html=True)
	
	nz_cols = st.columns(3)
	with nz_cols[0]:
		if st.button("View Dataset", key="nz_view"):
			st.info("Accessing PRJNA1332291 dataset...")
	with nz_cols[1]:
		if st.button("Time-series Analysis", key="nz_timeseries"):
			st.info("Loading temporal analysis tools...")
	with nz_cols[2]:
		if st.button("Site Map", key="nz_map"):
			st.info("Displaying NZ sampling locations...")
	
	# Dataset 3: California Current
	st.markdown("""
	<div style="border: 1px solid rgba(90,169,255,0.3); border-radius: 8px; padding: 20px; margin: 16px 0; background: rgba(90,169,255,0.05);">
		<h3 style="color: #5aa9ff; margin-bottom: 12px;">California Current Fish/Mammal eDNA (CalCOFI, PRJNA1322596)</h3>
		<p><strong>Description:</strong> COI/12S gene targeted for vertebrate detection (fish & cetaceans)</p>
		<p><strong>Spatial Coverage:</strong> Collection date, latitude/longitude, depth per sample</p>
		<div style="display: flex; gap: 20px; margin: 12px 0;">
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">156 SRA Experiments</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">707 BioSamples</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">Vertebrate Focus</span>
		</div>
		<p><strong>Institution:</strong> Scripps Institution of Oceanography</p>
	</div>
	""", unsafe_allow_html=True)
	
	calcofi_cols = st.columns(3)
	with calcofi_cols[0]:
		if st.button("Explore Dataset", key="calcofi_view"):
			st.info("Opening CalCOFI dataset browser...")
	with calcofi_cols[1]:
		if st.button("Vertebrate Analysis", key="calcofi_vertebrate"):
			st.info("Loading fish & cetacean detection results...")
	with calcofi_cols[2]:
		if st.button("Spatial Data", key="calcofi_spatial"):
			st.info("Displaying California Current sampling grid...")
	
	# Dataset 4: Japanese Coastal
	st.markdown("""
	<div style="border: 1px solid rgba(90,169,255,0.3); border-radius: 8px; padding: 20px; margin: 16px 0; background: rgba(90,169,255,0.05);">
		<h3 style="color: #5aa9ff; margin-bottom: 12px;">Japanese Coastal MiFish Survey (PRJDB7110)</h3>
		<p><strong>Description:</strong> Metabarcoding of Japanese sea communities using MiFish primer panels</p>
		<p><strong>Coverage:</strong> Rich coastal, deep water, seasonal data</p>
		<div style="display: flex; gap: 20px; margin: 12px 0;">
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">294 SRA Runs</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">MiFish Primers</span>
			<span style="background: rgba(90,169,255,0.2); padding: 4px 12px; border-radius: 12px;">Seasonal Coverage</span>
		</div>
		<p><strong>Focus:</strong> Japanese coastal marine communities</p>
	</div>
	""", unsafe_allow_html=True)
	
	japan_cols = st.columns(3)
	with japan_cols[0]:
		if st.button("Access Dataset", key="japan_view"):
			st.info("Connecting to PRJDB7110...")
	with japan_cols[1]:
		if st.button("MiFish Analysis", key="japan_mifish"):
			st.info("Loading MiFish primer analysis...")
	with japan_cols[2]:
		if st.button("Seasonal Trends", key="japan_seasonal"):
			st.info("Displaying seasonal biodiversity patterns...")
	
	# Data Categories Section
	st.markdown("## Data Categories")
	
	categories_cols = st.columns(2)
	with categories_cols[0]:
		st.markdown("""
		### Sequence Data Types
		- **Raw sequence reads** (FASTQ, SRA format)
		- **Multispecies amplicon data** (targeted gene regions)
		- **Metagenomic data** (whole community sequencing)
		- **Water column eDNA** (pelagic samples)
		- **Sediment eDNA** (benthic samples)
		""")
		
	with categories_cols[1]:
		st.markdown("""
		### Metadata Categories
		- **Spatial metadata** (lat/lon, region, ocean basin, sample site)
		- **Temporal metadata** (date, season, collection time)
		- **Depth gradient data** (surface to deep-sea)
		- **Environmental parameters** (temperature, salinity, pH)
		- **Sample processing** (filtration, extraction methods)
		""")
	
	# Reference Databases Section (Realistic Coverage)
	st.markdown("## Reference Database Coverage")
	
	ref_db_cols = st.columns(4)
	with ref_db_cols[0]:
		st.markdown("""
		### SILVA Deep-Sea Coverage
		**Limited Abyssal Representation**
		- ~2,400 deep-sea taxa
		- Bias toward shallow species
		- ~15% deep-sea specific
		- Reference gaps common
		""")
		
	with ref_db_cols[1]:
		st.markdown("""
		### WoRMS Marine Taxonomy
		**Incomplete Deep-Sea Coverage**
		- 240K total marine species
		- ~72K deep-sea described
		- ~30% with sequence data
		- Many undescribed species
		""")
		
	with ref_db_cols[2]:
		st.markdown("""
		### GenBank Deep-Sea Sequences
		**Quality & Coverage Issues**
		- ~180K deep-sea sequences
		- Variable sequence quality
		- Taxonomic misassignments
		- Geographic sampling bias
		""")
		
	with ref_db_cols[3]:
		st.markdown("""
		### Coverage Limitations
		**Unmatched Sequences**
		- ~40% reads unmatched
		- Novel candidate taxa
		- Expert review required
		- Ongoing updates needed
		""")
	
	# Database Limitations Warning
	st.error("""
	**🚨 Deep-Sea Reference Database Limitations:**
	- Reference coverage: ~30% of known deep-sea taxa have sequence data
	- Environmental inhibitors reduce sequence quality (85% QC pass rate)
	- High-pressure, low-temperature DNA degradation affects results
	- Geographic and depth sampling biases in existing databases
	- Many deep-sea lineages completely absent from references
	""")
	
	# Supplemental Datasets Section
	st.markdown("## Supplemental Datasets")
	
	st.markdown("""
	### Marine Plankton Metagenome Collection
	**Open-access marine eDNA metagenomics with over 18,000 runs via SRA**
	
	This comprehensive collection includes:
	- Global ocean sampling campaigns
	- Seasonal and depth-stratified sampling
	- Multiple size fractions (pico-, nano-, micro-plankton)
	- Associated environmental metadata
	- Cross-referenced with oceanographic databases
	""")
	
	if st.button("Explore SRA Marine eDNA Collection", use_container_width=True):
		st.info("Redirecting to SRA marine eDNA browser with 18,000+ datasets...")
	
	# Dataset Statistics Dashboard
	st.markdown("## Database Statistics")
	
	stats_cols = st.columns(4)
	with stats_cols[0]:
		st.metric("Total Datasets", "1,247", "+23 this month")
	with stats_cols[1]:
		st.metric("SRA Experiments", "18,456", "+342 this month")
	with stats_cols[2]:
		st.metric("Total Sequences", "847M", "+12M this month")
	with stats_cols[3]:
		st.metric("Data Volume", "2.4 TB", "+89 GB this month")
	
	# Large Dataset Handling
	st.markdown("## Large Dataset Support")
	
	st.markdown("""
	### Handling Multi-Gigabyte Marine eDNA Datasets
	
	MarineTaxaAI is designed to handle the large-scale datasets common in marine eDNA research:
	
	- **File Size Support:** Up to 5GB per file upload
	- **Batch Processing:** Multiple large files simultaneously
	- **Compressed Formats:** .gz, .bz2, .zip support for efficient transfer
	- **Memory Optimization:** Streaming processing for large FASTQ files
	- **Progress Tracking:** Real-time upload and processing status
	
	**Typical Marine eDNA Dataset Sizes:**
	- Single MiSeq run: 1-3 GB
	- HiSeq run: 10-50 GB
	- NovaSeq run: 100-500 GB
	- Metagenomic assemblies: 5-20 GB
	""")
	
	# Advanced Search and Tools
	st.markdown("## Advanced Tools & API Access")
	
	tools_cols = st.columns(3)
	with tools_cols[0]:
		st.markdown("""
		### Batch Download Tools
		- **SRA Toolkit integration**
		- **Bulk metadata export**
		- **Custom dataset compilation**
		- **API endpoint access**
		- **Programmatic queries**
		""")
		
	with tools_cols[1]:
		st.markdown("""
		### Analysis Pipelines
		- **Quality control workflows**
		- **Taxonomic assignment**
		- **Diversity analysis**
		- **Comparative studies**
		- **Statistical frameworks**
		""")
		
	with tools_cols[2]:
		st.markdown("""
		### Visualization Tools
		- **Interactive maps**
		- **Temporal analysis**
		- **Phylogenetic trees**
		- **Diversity plots**
		- **Custom dashboards**
		""")
	
	# Dataset Submission
	st.markdown("## Submit Your Dataset")
	
	submission_cols = st.columns(2)
	with submission_cols[0]:
		st.markdown("""
		### Data Submission Guidelines
		
		**Accepted Data Types:**
		- Raw sequencing data (FASTQ)
		- Processed amplicon data
		- Metagenomic assemblies
		- Associated metadata
		
		**Required Information:**
		- Sampling coordinates (lat/lon)
		- Collection date and time
		- Environmental parameters
		- Sequencing platform details
		- Gene markers used
		""")
		
	with submission_cols[1]:
		st.markdown("""
		### Submission Process
		
		1. **Prepare metadata** using our template
		2. **Upload raw data** to SRA/ENA
		3. **Submit to MarineTaxaAI** for integration
		4. **Quality review** by our curation team
		5. **Publication** in database with DOI
		
		**Benefits:**
		- Increased visibility and citations
		- Integration with analysis tools
		- Long-term preservation
		- Community access
		""")
	
	submit_cols = st.columns(2)
	with submit_cols[0]:
		if st.button("Download Metadata Template", use_container_width=True):
			st.info("Downloading MarineTaxaAI metadata template...")
	with submit_cols[1]:
		if st.button("Start Submission Process", use_container_width=True):
			st.info("Opening dataset submission portal...")

with _tab_expert_review:
	st.markdown("# Expert Review Workflow")
	st.markdown("*Collaborative validation of novel taxa discoveries by marine taxonomists*")
	
	# Expert Dashboard
	st.markdown("## Expert Review Dashboard")
	
	expert_stats_cols = st.columns(4)
	with expert_stats_cols[0]:
		st.metric("Pending Reviews", "47", "+12 this week")
	with expert_stats_cols[1]:
		st.metric("Validated Novel Taxa", "189", "+8 this week")
	with expert_stats_cols[2]:
		st.metric("Active Experts", "23", "Global network")
	with expert_stats_cols[3]:
		st.metric("Average Review Time", "2.3 days", "Per cluster")
	
	# Clusters Pending Review
	st.markdown("## Clusters Pending Expert Review")
	
	# Simulated review data
	review_data = pd.DataFrame({
		"Cluster_ID": [f"DeepSea_C{str(i).zfill(3)}" for i in [47, 52, 61, 73, 89, 94, 102, 115, 127, 134]],
		"Sequences": [23, 45, 12, 67, 34, 89, 18, 56, 41, 29],
		"Novelty_Score": [0.92, 0.89, 0.94, 0.87, 0.91, 0.96, 0.88, 0.93, 0.85, 0.90],
		"Depth_Range": ["4000-6000m", "2000-3000m", "6000-8000m", "1500-2500m", "3000-4000m", "7000-9000m", "1000-1500m", "4500-5500m", "2500-3500m", "3500-4500m"],
		"Location": ["Mariana Trench", "Mid-Atlantic Ridge", "Puerto Rico Trench", "Azores Plateau", "Canary Basin", "Japan Trench", "Iberian Margin", "Kermadec Trench", "Rockall Trough", "Hatteras Plain"],
		"Priority": ["High", "Medium", "High", "Low", "Medium", "High", "Low", "High", "Medium", "Medium"],
		"Days_Pending": [3, 7, 1, 12, 5, 2, 15, 4, 8, 6],
		"Assigned_Expert": ["Dr. Sarah Chen", "Dr. Marcus Silva", "Dr. Elena Kowalski", "Unassigned", "Dr. Raj Patel", "Dr. Yuki Tanaka", "Unassigned", "Dr. Maria Santos", "Dr. James Wilson", "Dr. Lisa Zhang"]
	})
	
	# Filter and sort options
	filter_cols = st.columns(3)
	with filter_cols[0]:
		priority_filter = st.selectbox("Priority Filter", ["All", "High", "Medium", "Low"])
	with filter_cols[1]:
		assignment_filter = st.selectbox("Assignment Status", ["All", "Assigned", "Unassigned"])
	with filter_cols[2]:
		sort_by = st.selectbox("Sort By", ["Days Pending", "Novelty Score", "Priority", "Sequences"])
	
	# Apply filters
	filtered_review = review_data.copy()
	if priority_filter != "All":
		filtered_review = filtered_review[filtered_review["Priority"] == priority_filter]
	if assignment_filter == "Assigned":
		filtered_review = filtered_review[filtered_review["Assigned_Expert"] != "Unassigned"]
	elif assignment_filter == "Unassigned":
		filtered_review = filtered_review[filtered_review["Assigned_Expert"] == "Unassigned"]
	
	st.dataframe(filtered_review, use_container_width=True)
	
	# Individual Cluster Review Interface
	st.markdown("## Cluster Review Interface")
	
	if st.selectbox("Select Cluster for Review", [""] + filtered_review["Cluster_ID"].tolist()):
		selected_cluster = st.selectbox("Select Cluster for Review", [""] + filtered_review["Cluster_ID"].tolist())
		
		if selected_cluster:
			cluster_info = filtered_review[filtered_review["Cluster_ID"] == selected_cluster].iloc[0]
			
			review_cols = st.columns(2)
			with review_cols[0]:
				st.markdown(f"""
				### Cluster Details: {selected_cluster}
				- **Sequences:** {cluster_info['Sequences']}
				- **Novelty Score:** {cluster_info['Novelty_Score']}
				- **Location:** {cluster_info['Location']}
				- **Depth Range:** {cluster_info['Depth_Range']}
				- **Priority:** {cluster_info['Priority']}
				- **Days Pending:** {cluster_info['Days_Pending']}
				""")
				
				# Representative sequence (simulated)
				st.markdown("**Representative Sequence:**")
				st.code("ATCGATCGATCGATCGTAGCTAGCTAGCTAGCTACGATCGATCGATCG...", language="text")
				
			with review_cols[1]:
				st.markdown("### Expert Review Form")
				
				expert_decision = st.radio(
					"Review Decision",
					["Novel Taxa (Confirmed)", "Known Taxa (Existing)", "Needs More Data", "Contamination/Artifact"]
				)
				
				confidence = st.slider("Confidence Level", 0, 100, 85)
				
				taxonomic_assignment = st.text_input("Suggested Taxonomic Assignment (if known)")
				
				expert_comments = st.text_area("Expert Comments", height=100)
				
				if st.button("Submit Review", use_container_width=True):
					st.success(f"Review submitted for {selected_cluster}!")
					st.info(f"Decision: {expert_decision} (Confidence: {confidence}%)")
	
	# Expert Network
	st.markdown("## Global Expert Network")
	
	expert_network_cols = st.columns(3)
	with expert_network_cols[0]:
		st.markdown("""
		### Deep-Sea Taxonomists
		- **Dr. Sarah Chen** - Mariana Trench specialist
		- **Dr. Marcus Silva** - Atlantic deep-water fauna
		- **Dr. Elena Kowalski** - Arctic deep-sea biology
		- **Dr. Yuki Tanaka** - Pacific trench systems
		""")
		
	with expert_network_cols[1]:
		st.markdown("""
		### Molecular Biologists
		- **Dr. Raj Patel** - eDNA methodology
		- **Dr. Maria Santos** - Phylogenetic analysis
		- **Dr. James Wilson** - Metabarcoding expert
		- **Dr. Lisa Zhang** - Bioinformatics specialist
		""")
		
	with expert_network_cols[2]:
		st.markdown("""
		### Review Statistics
		- **Total Reviews:** 1,247
		- **Novel Taxa Confirmed:** 189 (15.2%)
		- **Known Taxa Identified:** 834 (66.9%)
		- **Needs More Data:** 156 (12.5%)
		- **Artifacts Removed:** 68 (5.5%)
		""")
	
	# Validation Metrics (Realistic)
	st.markdown("## Validation Performance Metrics")
	
	validation_cols = st.columns(4)
	with validation_cols[0]:
		st.metric("True Novelty Recall", "70% (±5%)", "Expert validated")
	with validation_cols[1]:
		st.metric("False Discovery Rate", "~30%", "Novel taxa FDR")
	with validation_cols[2]:
		st.metric("Inter-expert Agreement", "78%", "Cohen's kappa")
	with validation_cols[3]:
		st.metric("Review Turnaround", "5-7 days", "Average time")
	
	# Validation Limitations
	st.warning("""
	**Validation Challenges:**
	- Expert disagreement common for novel deep-sea taxa
	- Limited morphological data for validation
	- Seasonal and geographic variation affects consistency
	- Conservative bias in novel taxa confirmation
	""")

with _tab_research:
	st.markdown("# Research Hub")
	st.markdown("*Advanced tools and resources for deep-sea eDNA research*")
	
	# Research Overview
	st.markdown("## Deep-Sea eDNA Research Platform")
	
	st.markdown("""
	### Platform Overview
	
	MarineTaxa.ai is a comprehensive platform for analyzing environmental DNA from deep-sea environments, 
	specifically designed to address the challenges of biodiversity discovery in data-scarce ecosystems.
	
	**Key Capabilities:**
	1. **Taxonomy-Free Analysis** - Advanced clustering without reference database dependence
	2. **Novel Taxa Discovery** - AI-powered identification of unknown species
	3. **Environmental Integration** - Deep-sea metadata and bathymetric analysis
	4. **Expert Collaboration** - Global network of marine taxonomists
	""")
	
	# Technical Architecture
	st.markdown("## Technical Architecture")
	
	arch_cols = st.columns(2)
	with arch_cols[0]:
		st.markdown("""
		### Core Components
		- **AI Processing Pipeline** - DNABERT-2 + HDBSCAN clustering
		- **Novelty Detection Engine** - Autoencoder-based scoring
		- **Environmental Integration** - Depth, pressure, temperature analysis
		- **Real-time Monitoring** - GPU utilization and throughput tracking
		- **Expert Review System** - Collaborative validation workflow
		""")
		
	with arch_cols[1]:
		st.markdown("""
		### Performance Specifications
		- **Processing Speed:** ~500 seq/min (GPU), ~100 seq/min (CPU)
		- **Deep-Sea Assignment:** 60-75% species-level accuracy
		- **Novelty Detection TPR:** 70% (±5%)
		- **False Discovery Rate:** ~30% for novel taxa
		- **File Size Support:** Up to 5GB per upload
		- **Depth Range:** 200-11,000 meters
		""")
		
		# Performance Disclaimer
		st.info("""
		**Model Performance Disclaimer:**
		- Accuracy validated on Arctic and abyssal datasets
		- ROC curves and confusion matrices available
		- Performance varies with environmental conditions
		- Ongoing model updates as new data becomes available
		""")
	
	# Research Applications
	st.markdown("## Research Applications")
	
	app_cols = st.columns(3)
	with app_cols[0]:
		st.markdown("""
		### Marine Conservation
		- Rapid biodiversity assessment
		- Ecosystem health monitoring
		- Protected area designation
		- Impact assessment studies
		""")
		
	with app_cols[1]:
		st.markdown("""
		### Scientific Discovery
		- Novel species identification
		- Phylogenetic analysis
		- Biogeographic studies
		- Evolutionary research
		""")
		
	with app_cols[2]:
		st.markdown("""
		### Environmental Monitoring
		- Climate change impacts
		- Ocean acidification effects
		- Pollution assessment
		- Habitat degradation tracking
		""")
	
	# Collaboration Network
	st.markdown("## Global Research Network")
	
	network_cols = st.columns(2)
	with network_cols[0]:
		st.markdown("""
		### Research Institutions
		- **Woods Hole Oceanographic Institution** - Deep-sea exploration
		- **Scripps Institution of Oceanography** - Marine biodiversity
		- **National Institute of Oceanography** - Indian Ocean studies
		- **Alfred Wegener Institute** - Polar and deep-sea research
		""")
		
	with network_cols[1]:
		st.markdown("""
		### Expert Contributors
		- **23 Active Taxonomists** - Global deep-sea specialists
		- **15 Molecular Biologists** - eDNA methodology experts
		- **8 Bioinformaticians** - Computational analysis specialists
		- **12 Field Researchers** - Sample collection and validation
		""")
	
	# Data Standards & Protocols
	st.markdown("## Data Standards & Protocols")
	
	standards_cols = st.columns(2)
	with standards_cols[0]:
		st.markdown("""
		### Data Formats
		- **FASTA/FASTQ** - Raw sequence data
		- **Compressed formats** - .gz, .bz2, .zip support
		- **Metadata standards** - Darwin Core compliance
		- **Quality metrics** - Phred scores and filtering
		""")
		
	with standards_cols[1]:
		st.markdown("""
		### Analysis Protocols
		- **Quality control** - Automated filtering pipelines
		- **Clustering methods** - HDBSCAN with environmental features
		- **Validation procedures** - Expert review workflows
		- **Reproducibility** - Version-controlled analysis parameters
		""")
	
	# API & Integration
	st.markdown("## API & Integration")
	
	api_cols = st.columns(3)
	with api_cols[0]:
		st.markdown("""
		### REST API
		- Programmatic access to analysis pipeline
		- Batch processing capabilities
		- Real-time status monitoring
		- Result retrieval and export
		""")
		
	with api_cols[1]:
		st.markdown("""
		### Data Integration
		- NCBI SRA connectivity
		- OBIS database linking
		- WoRMS taxonomic validation
		- Custom database imports
		""")
		
	with api_cols[2]:
		st.markdown("""
		### Export Options
		- CSV/TSV data tables
		- FASTA sequence files
		- Phylogenetic trees (Newick)
		- Analysis reports (PDF)
		""")
	
	# Getting Started
	st.markdown("## Getting Started")
	
	start_cols = st.columns(3)
	with start_cols[0]:
		if st.button("Tutorial & Documentation", use_container_width=True):
			st.info("Opening comprehensive user guide...")
	with start_cols[1]:
		if st.button("Sample Data Download", use_container_width=True):
			st.info("Downloading example deep-sea eDNA datasets...")
	with start_cols[2]:
		if st.button("Contact Research Team", use_container_width=True):
			st.info("Connecting with our research collaboration team...")

# Additional Research Content
with st.expander("Research Publications", expanded=False):
	st.markdown("# Deep-Sea eDNA Research Publications")
	st.markdown("*Specialized collection focusing on deep-sea eDNA challenges, AI-driven novel species detection, and taxonomy-free methods*")
	
	# Search and filter interface
	st.markdown("## Search & Filter Publications")
	
	search_cols = st.columns(4)
	with search_cols[0]:
		topic_filter = st.selectbox("Topic", ["All", "AI Novelty Detection", "Taxonomy-Free Methods", "Deep-Sea Challenges", "Database Independence", "GPU Optimization", "Misclassification Issues", "Sample Preservation"], key="topic_filter_publications")
	with search_cols[1]:
		year_filter = st.selectbox("Year", ["All", "2025", "2024", "2023", "2022", "2021"], key="year_filter_publications")
	with search_cols[2]:
		journal_filter = st.selectbox("Journal", ["All", "Frontiers in Ocean Sustainability", "Ecological Indicators", "Molecular Ecology Resources", "PeerJ", "Bioinformatics", "Environmental DNA", "Scientific Reports"], key="journal_filter_publications")
	with search_cols[3]:
		method_filter = st.selectbox("Method Focus", ["All", "Autoencoder Detection", "DNABERT Embeddings", "HDBSCAN Clustering", "GPU Acceleration", "Reference Independence"], key="method_filter_publications")
	
	# Search bar
	search_query = st.text_input("Search papers by keywords, authors, or title", placeholder="e.g., novelty detection, taxonomy-free, deep-sea, autoencoder")
	
	# Featured/Highlighted Papers
	st.markdown("## Featured Breakthrough Papers")
	
	featured_cols = st.columns(2)
	with featured_cols[0]:
		st.markdown("""
		### Editor's Pick: Integrative Deep-Sea Assessment
		**Framing Cutting-Edge Integrative Deep-Sea Biodiversity Assessment**
		
		*Smith, J.; Martínez, L.; Zhao, Y. (2025). Frontiers in Ocean Sustainability*
		
		Integrates eDNA, imaging, and acoustic data to map deep-sea biodiversity across trenches and seamounts. Shows methods for sample preservation under high pressure and hybrid data fusion workflows.
		
		**Keywords:** deep-sea biodiversity, integrative assessment, high-pressure preservation
		""")
		
	with featured_cols[1]:
		st.markdown("""
		### AI Breakthrough: Taxonomy-Free Assessment
		**AI for Taxonomy-Free Biodiversity Assessment**
		
		*Lee, K.; Patel, R.; Nguyen, A. (2024). Ecological Indicators*
		
		Demonstrates unsupervised clustering of eDNA sequence embeddings to estimate biodiversity without reference databases. Validates cluster-based diversity indices against manual curation.
		
		**Keywords:** AI, taxonomy-free, unsupervised clustering, sequence embeddings
		""")
	

# Footer
st.markdown("<div class='mtx-footer'>India · Powered by MarineTaxa.ai · Research-first eDNA analytics</div>", unsafe_allow_html=True)



