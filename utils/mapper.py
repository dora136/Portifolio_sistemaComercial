





class mapper_crm:
    
    def __init__(self):

        self.mapa_provedor_deal = {
            "AWS": 363,
            "AZURE": 365,
            "GCP": 343,
            "DIGITAL OCEAN": 415,
            "ORACLE CLOUD": 355,
            "IBM CLOUD": 347,
            "ALIBABA CLOUD": 405,
            "HEROKU": 411,
            "VERCEL": 345,
            "NETLIFY": 409,
            "CLOUDFLARE": 357,
            "LINODE": 359,
            "VULTR": 361,
        }
        
        self.mapa_etapa_lead = {
            "Follow SDR": "PROCESSED",
        }

        self.mapa_segmento = {
            "SaaS": "IT",
            "Fintech": "FINANCE",
            "E-commerce": "RETAIL",
            "Healthtech": "HEALTHCARE",
            "Edtech": "EDUCATION",
            "Logística": "LOGISTICS",
            "Indústria": "MANUFACTURING",
            "Varejo": "RETAIL_STORE",
            "Governo": "GOVERNMENT",
            "Telecomunicações": "TELECOM",
            "Serviços": "SERVICES",
            "Consultoria": "CONSULTING",
            "Outro": "OTHER"
        }

    def name_to_id(self, name, tipo):

        mapa = getattr(self, f'mapa_{tipo}')

        id_mapped = mapa.get(name, None)
        
        return id_mapped


    def id_to_name(self, id, tipo):
        
        mapa = getattr(self, f'mapa_{tipo}')
        # Inverte o dicionário para busca reversa
        mapa_invertido = {v: k for k, v in mapa.items()}

        name_mapped = mapa_invertido.get(id, None)
 
        return name_mapped


mapper_b = mapper_crm()