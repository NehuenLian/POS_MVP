import datetime as dtime
from collections import Counter

from src.database.session_manager import session_scope
from src.repository.sale_details_dao import SalesDetailsDAO
from src.repository.sales_dao import SalesDAO
from src.repository.stock_dao import StockDAO
from src.utils.logging_config import business_logger


class Product: # DTO
    product_instance_list = [] # TODO: Consider removing this list in the future to reduce redundancy; ProductSale.productsale_instances serves the same purpose.

    def __init__(self, product_id: int, barcode: str, product_name: str, available_quantity: int, customer_price: float):
        Product.product_instance_list.append(self)
        self.product_id = product_id
        self.barcode = barcode
        self.product_name = product_name
        self.available_quantity = available_quantity
        self.customer_price = customer_price

        print(Product.product_instance_list)

    def __hash__(self):
        return hash(self.product_id)
    
    def __eq__(self, other):
        if isinstance(other, Product):
            return self.product_id == other.product_id
        return False

    def __repr__(self):
        return (
            f"  ID: {self.product_id},\n"
            f"  Barcode: {self.barcode},\n"
            f"  Product Name: {self.product_name},\n"
            f"  Available Quantity: {self.available_quantity},\n"
            f"  Customer Price: ${self.customer_price}\n"
        )
    
    @classmethod
    def clear_product_instance_list(cls):
        cls.product_instance_list.clear()

class ProductSale:
    productsale_instances = []

    def __init__(self, product: Product):
        self.product = product
        self.subquantity = None
        self.subtotal = None
        ProductSale.productsale_instances.append(self)

    def __hash__(self):
        return hash(self.product.product_id)
    
    def __eq__(self, other):
        if isinstance(other, ProductSale):
            return self.product.product_id == other.product.product_id
        return False

    def __repr__(self) -> str:
        return (
            f"  Product: {self.product},\n"
            f"  Quantity: {self.subquantity},\n"
            f"  Subtotal: ${self.subtotal},\n"
            f"  ====================\n"
        )
    
    @classmethod
    def clear_productsale_instances(cls):
        cls.productsale_instances.clear()
    
    @classmethod
    def count_products_in_cart(cls) -> dict:
        business_logger.debug("Executing count_products_in_cart")
        """
        Counts the occurrences of each Product ID in the productsale_instances list.
        Returns a dictionary where the keys are product IDs and the values are the quantity.
        """
        product_ids = []
        for unit in cls.productsale_instances:
            product_ids.append(unit.product.product_id)
        product_count = Counter(product_ids)
        business_logger.info(f'Full product count(key:id, value: quantity): {product_count}')
        return product_count
    
    @classmethod
    def count_and_assign_quantity_by_product(cls, product_count: dict):
        business_logger.debug("Executing count_and_assign_quantity_by_product")
        for unit in cls.productsale_instances:
            quantity = product_count[unit.product.product_id] # Gets the count using the id as a index
            unit.subquantity = quantity
            
    @classmethod
    def calculate_and_assign_subtotal_to_each_product(cls, product_count: dict):
        business_logger.debug("Executing calculate_and_assign_subtotal_to_each_product")
        for unit in cls.productsale_instances:
            occurrence = product_count[unit.product.product_id]
            subtotal = unit.product.customer_price * occurrence

            unit.subtotal = subtotal

class SaleManagement:
    def __init__(self):
        self.sale_list = ProductSale.productsale_instances # List of product instances
        
        self.amount = None
        self.total_quantity = None
        self.pay_method = None
        self.sale_date = None
        self.sale_hour = None

        business_logger.info('Program flow started. [SALES MANAGEMENT]')

    def __repr__(self):
        return (
                f"  List: {self.sale_list},\n"
                f"  Total: ${self.amount},\n"
                f"  Total Product Quantity: {self.total_quantity},\n"
                f"  Pay method used: {self.pay_method}\n"
                f"  Date of sale: {self.sale_date}\n"
                f"  Hour of sale: {self.sale_hour}\n"
                )

    def clear_sale_list(self):
        self.sale_list.clear()

    def verify_barcode(self, barcode: str) -> int:
        with session_scope() as session:
            query = StockDAO(session)
            product_id = query.check_product_exists_by_barcode(barcode)
            if product_id:
                business_logger.debug(f'Product with (ID:{product_id} verified.)')

                return product_id

    def get_full_product(self, product_id: int) -> Product:
        with session_scope() as session:
            query = StockDAO(session)
            product_id, barcode, product_name, available_quantity, customer_price = query.get_product(product_id)
            product = Product(product_id, barcode, product_name, available_quantity, customer_price)
            business_logger.info(f'Barcode recovered:"{barcode}". Product exists. (ID:{product_id}) Product:"{product.product_name}" obtained from database.')
            if product.product_id:

                return product

    def create_product(self, product_id, barcode, product_name, available_quantity, customer_price): # Frontend
        Product(product_id, barcode, product_name, available_quantity, customer_price)
        business_logger.debug(
            f"A product was added with the following characteristics: "
            f"product_id={product_id}, barcode='{barcode}', product_name='{product_name}', "
            f"available_quantity={available_quantity}, customer_price=${customer_price}"
        )

    def cancel_product(self, id_to_cancel: int):
        for unit in Product.product_instance_list[:]:
            if id_to_cancel == unit.product_id:
                Product.product_instance_list.remove(unit)
                business_logger.info(f'Product "{unit.product_name}" (ID: {unit.product_id}) was removed from cart from user action.')
                break

    def set_pay_method(self, method_selected):
        self.pay_method = method_selected
        business_logger.info(f'Pay method selected: "{method_selected}"')

    def build_product_sale(self):
        """
        The DTO 'Product' transitions into a sales-state object, acquiring attributes such as 'subtotal' or 'quantity per product' (subquantity).
        """
        for unit in Product.product_instance_list:
            product_sale = ProductSale(unit)
        product_count = product_sale.count_products_in_cart()
        product_sale.count_and_assign_quantity_by_product(product_count)
        product_sale.calculate_and_assign_subtotal_to_each_product(product_count)

    def compute_total_quantity(self) -> int: # TODO: refactor
        total_quantity = len(self.sale_list)
        self.total_quantity = total_quantity
        business_logger.info(f'Total quantity: {total_quantity}')

        return self.total_quantity
    
    def compute_total_amount(self) -> float: # TODO: refactor
        prices = []
        for unit in self.sale_list:
            prices.append(unit.product.customer_price)
        amount = sum(prices)
        self.amount = amount
        business_logger.info(f'Sale amount: ${amount}')

        return amount
    
    def remove_duplicates(self):
        """
        Removes duplicate instances of products in the sale list, ensuring each product appears only once as a record in the database.
        """
        sale_with_no_duplicates = set()
        for unit in self.sale_list:
            sale_with_no_duplicates.add(unit)

        self.sale_list = list(sale_with_no_duplicates)

    def get_timestamp(self):
        now = dtime.datetime.now().replace(microsecond=0)
        self.sale_date = now.date()
        self.sale_hour = now.time().replace(microsecond=0)

    def prepare_sale_summary(self):
        self.compute_total_quantity()
        self.compute_total_amount()
        self.remove_duplicates()
        self.get_timestamp()

        print(f"El estado en este momento deberia tener todos los atributos: {self}")

class SalePersister:
    def __init__(self, sale: SaleManagement):
        self.sale = sale

    def get_products_dict(self) -> list:
        details_list = []
        for product in self.sale.sale_list:
            product_id = product.product.product_id
            unit_price = product.product.customer_price
            quantity = product.subquantity
            subtotal = product.subtotal

            details_list.append({'product_id' : product_id,
                                'unit_price' : unit_price,
                                'quantity' : quantity,
                                'subtotal' : subtotal})
        
        return details_list

    def insert_sale(self, session) -> int:
        insert_operation = SalesDAO(session)
        sale_id = insert_operation.insert_sale_record(
                            self.sale.total_quantity, 
                            self.sale.amount, 
                            self.sale.pay_method,
                            self.sale.sale_date, 
                            self.sale.sale_hour
                        )
        business_logger.info(f'Successfully inserted the record for (Sale ID: {sale_id}) in "Sales" table.')
        return sale_id

    def insert_sale_details(self, sale_id, details_list, session):
        insert_detail = SalesDetailsDAO(session)
        for product in details_list:
            insert_detail.insert_sale_detail(
                                sale_id,
                                product['product_id'],
                                product['quantity'],
                                product['unit_price'],
                                product['subtotal']
                            )
        business_logger.info(f'Successfully inserted the details for (Sale ID: {sale_id}) in "SalesDetails" table.')

    def update_inventory(self, details_list, session):
        update_inventory = StockDAO(session)
        for product in details_list:
            update_inventory.update_stock_table(
                            product['product_id'],
                            product['quantity']
                        )
        business_logger.info(f'Existences (Stock table) successfully updated.')

    def confirm_transaction(self):
        """
        Implements the Unit of Work design pattern to ensure atomic sales transactions.

        Steps:
            - Convert the product list into a dictionary (optimized for SQLAlchemy).
            - Insert general sale data into the 'sales' table and retrieve the sale ID using flush().
            - Insert sale details into the 'sales_details' table, linking them to the retrieved sale ID.
            - Update stock levels according to the purchased products.
            - Clear product and sales lists from memory after a successful transaction.
        """
        business_logger.info(f'Starting final transaction.')

        with session_scope() as session:
            details_list = self.get_products_dict()
            sale_id = self.insert_sale(session)
            self.insert_sale_details(sale_id, details_list, session)
            self.update_inventory(details_list, session)
            business_logger.info(f'[IMPORTANT] Transaction: {sale_id} successfully completed.')

            # Clear product lists
            Product.clear_product_instance_list()
            ProductSale.clear_productsale_instances()
            self.sale.clear_sale_list()



