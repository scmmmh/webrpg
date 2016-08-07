import { moduleForComponent, test } from 'ember-qunit';
import hbs from 'htmlbars-inline-precompile';

moduleForComponent('fd-accordion-item', 'Integration | Component | fd accordion item', {
  integration: true
});

test('it renders', function(assert) {
  // Set any properties with this.set('myProperty', 'value');
  // Handle any actions with this.on('myAction', function(val) { ... });

  this.render(hbs`{{fd-accordion-item}}`);

  assert.equal(this.$().text().trim(), '');

  // Template block usage:
  this.render(hbs`
    {{#fd-accordion-item}}
      template block text
    {{/fd-accordion-item}}
  `);

  assert.equal(this.$().text().trim(), 'template block text');
});
