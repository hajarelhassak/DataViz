from connectors.factory import SUPPORTED_ENGINES



class DatabaseEngineService:


    @staticmethod
    def get_supported_engines():

        return [

            {
                "id":engine,
                "label":engine.upper()
            }

            for engine in SUPPORTED_ENGINES

        ]