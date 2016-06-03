import { moduleForComponent, test } from 'ember-qunit';
import hbs from 'htmlbars-inline-precompile';

moduleForComponent('fd-dropdown-menu', 'Integration | Component | fd dropdown menu', {
  integration: true
});

test('it renders', function(assert) {
  // Set any properties with this.set('myProperty', 'value');
  // Handle any actions with this.on('myAction', function(val) { ... });

  this.render(hbs`{{fd-dropdown-menu}}`);

  assert.equal(this.$().text().trim(), '');

  // Template block usage:
  this.render(hbs`
    {{#fd-dropdown-menu}}
      template block text
    {{/fd-dropdown-menu}}
  `);

  assert.equal(this.$().text().trim(), 'template block text');
});
