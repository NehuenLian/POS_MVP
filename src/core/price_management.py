from src.database.session_manager import session_scope
from src.repository.stock_dao import StockDAO
from src.utils.logging_config import business_logger


class PriceManagement:
    def __init__(self):
        business_logger.info('Program flow started. [PRICE MANAGEMENT]')

    def search_product(self, barcode: str):
        with session_scope() as session:
            query = StockDAO(session)
            id, product_name, price = query.select_id_name_price(barcode)
            business_logger.info(f'Product found: "{product_name}" (ID: {id}) at ${price}')
            return [id, product_name, price]

    def update_prices(self, id: int, new_price: float):
        with session_scope() as session:
            query = StockDAO(session)
            query.update_price_in_db(id, new_price)
            business_logger.info(f'Updated price for Product (ID {id}): ${new_price}')
            business_logger.info('[IMPORTANT] PRICE SUCCESSFULLY UPDATED. PROCESS ENDED SUCCESSFULL.\n-')

