import operator
from client.states.client import RegisterUser
from db.models import Dish
from filters.base import is_button_selected
from aiogram.types import CallbackQuery
from aiogram_dialog import Window, DialogManager, Dialog
from aiogram_dialog.widgets.kbd import Multiselect, Button, Group, ManagedMultiSelectAdapter
from aiogram_dialog.widgets.text import Format, Const
from states.client import DishDialog
from keyboards.dialog.base_dialog_buttons import cancel_button, continue_button, default_nav
from keyboards.menu.kbds import request_contact_button_kbd

async def switch_page(c: CallbackQuery, b: Button, d: DialogManager):
    pagination_key = d.data['aiogd_context'].widget_data['navigate_button']
    if b.widget_id == "next_page":
        pagination_key += 5
    elif b.widget_id == "prev_page":
        if pagination_key > 4:
            pagination_key -= 5
        else:
            await c.answer("Дальше позиций нет😕")
    d.data['aiogd_context'].widget_data['navigate_button'] = pagination_key
    await d.switch_to(DishDialog.select_dish)

async def confirm_order(c: CallbackQuery, b: Button, d: DialogManager):
    details = "Отлично, вот детали заказа:\n"
    order = {"dishes": [], "summary": 0.0}
    for dish_id in d.data['aiogd_context'].widget_data['m_dish']:
        dish = Dish.objects.filter(id=dish_id).first()
        quantity = d.data['aiogd_context'].widget_data[f'dish_{dish_id}_quantity']
        dish_summary = dish.price * quantity
        details += f"{dish.name} х {quantity} ---- {dish_summary}Р\n"
        order['dishes'].append({"id": dish.id, "name": dish.name, "price":dish.price, 
                                 "quantity": quantity, "dish_summary": dish_summary})
        order['summary'] += dish_summary
    details += f"""Если всё верно, нажми на кнопку оформить, и мы оформим заказ. 
Если нет - нажми на кнопку отмена, и всё отменится.

Итого: {order['summary']}Р"""
    await c.message.delete()
    await c.message.answer(details, reply_markup=request_contact_button_kbd)
    await d.data['state'].update_data({"order": order})
    await d.mark_closed()
    await RegisterUser.send_contact.set()

async def get_dishes(**kwargs):
    if not 'navigate_button' in list(kwargs['aiogd_context'].widget_data.keys()):
        kwargs['aiogd_context'].widget_data['navigate_button'] = 0
    dish_list = Dish.objects.all()
    start = kwargs['aiogd_context'].widget_data['navigate_button']
    end = start + 5
    try:
        return {"dishes": [(f"{dish.name}, {dish.price}", dish.id) for dish in dish_list[start:end]]}
    except IndexError:
        return {"dishes": [(f"{dish.name}, {dish.price}", dish.id) for dish in dish_list[start:-1]]}

@is_button_selected(key='m_dish')
async def switch_to_dish_details(c: CallbackQuery, b: Button, d: DialogManager):
    await d.switch_to(DishDialog.confirm_order)

async def edit_quantity(c: CallbackQuery, m: ManagedMultiSelectAdapter, d: DialogManager, b: str):
    d.data['aiogd_context'].widget_data['current'] = b
    await d.switch_to(DishDialog.edit_dish_quantity)

dish_list = Window(Const("Привет👋! Я помогу тебе сделать заказ. Пожалуйста, выбери нужные позиции из списка:"),
                   Group(Multiselect(Format("✅{item[0]}"),
                                     Format("{item[0]}"),
                                     id="m_dish", items='dishes', on_click=edit_quantity,
                                     item_id_getter=operator.itemgetter(1)), 
                         width=1),
                   Group(Button(Const("<"), on_click=switch_page, id="prev_page"),
                         Button(Const(">"), on_click=switch_page, id="next_page"),
                         width=2),
                   Button(continue_button,
                          on_click=confirm_order,
                          id='continue'),
                          cancel_button,
                          getter=get_dishes,
                          state=DishDialog.select_dish)

async def get_quantity_for_dish(**kwargs):
    for key in kwargs['aiogd_context'].widget_data.keys():
        if key.startswith('current'):
            dish_id = kwargs['aiogd_context'].widget_data[key]
            dish = Dish.objects.filter(id=dish_id).first()
            if not f'dish_{dish_id}_quantity' in kwargs['aiogd_context'].widget_data.keys():
                kwargs['aiogd_context'].widget_data[f'dish_{dish_id}_quantity'] = 1
            quantity = kwargs['aiogd_context'].widget_data[f'dish_{dish_id}_quantity']
            dct = {"dish": dish, "quantity": quantity, "dish_summary": dish.price * quantity}
            break
    return dct

async def change_quantity(c: CallbackQuery, b: Button, d: DialogManager):
    current_dish_id = d.data['aiogd_context'].widget_data['current']
    current_dish_quantity = d.data['aiogd_context'].widget_data[f'dish_{current_dish_id}_quantity']
    match b.widget_id:
        case "decrease":
            if current_dish_quantity < 1:
                await c.answer("Нелья заказать меньше 0")
            else:
                current_dish_quantity -= 1
        case "increase":
            current_dish_quantity += 1
    d.data['aiogd_context'].widget_data[f'dish_{current_dish_id}_quantity'] = current_dish_quantity
    await d.switch_to(DishDialog.edit_dish_quantity)

async def switch_to_list(c: CallbackQuery, b: Button, d: DialogManager):
    current_dish_id = d.data['aiogd_context'].widget_data['current']
    current_dish_quantity = d.data['aiogd_context'].widget_data[f'dish_{current_dish_id}_quantity']
    dial = d.dialog()
    m_button = dial.find('m_dish')
    if current_dish_quantity == 0:
        await m_button.set_checked(None, d.data['aiogd_context'].widget_data['current'], False, d)
    else:
        await m_button.set_checked(None, d.data['aiogd_context'].widget_data['current'], True, d)
    await d.switch_to(DishDialog.select_dish)

quantity_edit = Window(Const(text="Выберите необходимое количество:"),
                       Format(text="{dish.name}, {quantity}шт., {dish_summary}P"),
                       Group(Button(Const(text="-"), on_click=change_quantity, id='decrease'),
                             Button(Const(text='+'), on_click=change_quantity, id='increase'),
                             width=2),
                       Button(continue_button, on_click=switch_to_list,
                              id='continue'),
                       cancel_button,
                       getter=get_quantity_for_dish,
                       state=DishDialog.edit_dish_quantity)


async def get_dish_detail(**kwargs):
    details = ""
    dishes = {"dishes": [], "summary": 0.0}
    for dish_id in kwargs['aiogd_context'].widget_data['m_dish']:
        dish = Dish.objects.filter(id=dish_id).first()
        quantity = kwargs['aiogd_context'].widget_data[f'dish_{dish_id}_quantity']
        dish_summary = dish.price * quantity
        details += f"{dish.name} х {quantity} ---- {dish_summary}Р\n"
        dishes['dishes'].append({"id": dish.id,"name": dish.name, "price":dish.price, 
                                 "quantity": quantity, "dish_summary": dish_summary})
        dishes['summary'] += dish_summary
    details += f"""Итого: {dishes['summary']}Р
Если всё верно, нажми на кнопку продолжить, мы оформим заказ."""
    return {"details": details}



order_summary =  Window(Format("Отлично, вот детали заказа:\n{details}"),
                        Button(continue_button, id='continue', on_click=confirm_order),
                        default_nav,
                        getter=get_dish_detail,
                        state=DishDialog.confirm_order)

dish_dialog = Dialog(dish_list, quantity_edit, order_summary)